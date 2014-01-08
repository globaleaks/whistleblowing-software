# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import re

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

# override GLSetting
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import files, authentication, submission, wbtip
from globaleaks.handlers.base import DownloadToken
from globaleaks.handlers.admin import create_context, update_context, create_receiver, get_receiver_list
from globaleaks.rest import errors
from globaleaks.models import InternalTip

from io import BytesIO as StringIO

import time

@transact_ro
def collect_ifile_as_wb_without_wbtip(store, internaltip_id):
    file_list = []
    itip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    for internalfile in itip.internalfiles:
        file_list.append(wbtip.wb_serialize_file(internalfile))
    return file_list


class TestSubmission(helpers.TestGL):

    def setUp(self):

        filename = ''.join(unichr(x) for x in range(0x400, 0x4FF))
        body = ''.join(unichr(x) for x in range(0x370, 0x3FF))

        self.dummyFile1 = {}
        self.dummyFile1['body'] = StringIO()
        self.dummyFile1['body'].write(body[0:GLSetting.defaults.maximum_textsize].encode('utf-8'))
        self.dummyFile1['body_len'] = len(self.dummyFile1['body'].getvalue())
        self.dummyFile1['content_type'] = 'application/octect'
        self.dummyFile1['filename'] = 'aaaaaa'

        self.dummyFile2 = {}
        self.dummyFile2['body'] = StringIO()
        self.dummyFile2['body'].write(str('aaaaba'))
        self.dummyFile2['body_len'] = len(self.dummyFile2['body'].getvalue())
        self.dummyFile2['content_type'] = 'application/octect'
        self.dummyFile2['filename'] = filename[0:GLSetting.defaults.maximum_namesize]

        return self._setUp()

    # --------------------------------------------------------- #
    @inlineCallbacks
    def test_create_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['submission_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        retval = re.match(self.dummyContext['receipt_regexp'], receipt)
        self.assertTrue(retval)

    @inlineCallbacks
    def test_fail_submission_missing_file(self):

        mycopy = dict(self.dummyContext)
        mycopy['file_required'] = True

        for attrname in models.Context.localized_strings:
            mycopy[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        context_status = yield create_context(mycopy)
        submission_desc = dict(self.dummySubmission)

        submission_desc['context_gus'] = context_status['context_gus']
        submission_desc['finalize'] = True
        submission_desc['wb_fields'] = helpers.fill_random_fields(self.dummyContext)

        try:
            yield submission.create_submission(submission_desc, finalize=True)
        except errors.FileRequiredMissing:
            self.assertTrue(True)
            return
        self.assertTrue(False)

    @inlineCallbacks
    def emulate_file_upload(self, associated_submission_id):

        (relationship1, cksum1, size1) = yield threads.deferToThread(files.dump_file_fs, self.dummyFile1)
        self.assertEqual(size1, self.dummyFile1['body_len'])
        self.registered_file1 = yield files.register_file_db(
            self.dummyFile1, relationship1, cksum1, associated_submission_id,
        )

        (relationship2, cksum2, size2) = yield threads.deferToThread(files.dump_file_fs, self.dummyFile2)
        self.assertEqual(size2, self.dummyFile2['body_len'])
        self.registered_file2 = yield files.register_file_db(
            self.dummyFile2, relationship2, cksum2, associated_submission_id,
            )

        # well... why not ? :
        self.assertNotEqual(size1, self.dummyFile2['body_len'])



    @inlineCallbacks
    def test_create_internalfiles(self):
        yield self.emulate_file_upload(self.dummySubmission['submission_gus'])
        keydiff = {'size', 'content_type', 'name', 'creation_date', 'id'} - set(self.registered_file1.keys())
        self.assertFalse(keydiff)
        keydiff = {'size', 'content_type', 'name', 'creation_date', 'id'} - set(self.registered_file2.keys())
        self.assertFalse(keydiff)

    @transact
    def _force_finalize(self, store, submission_id):
        it = store.find(models.InternalTip, models.InternalTip.id == submission_id).one()
        it.mark = models.InternalTip._marker[1] # 'finalized'

    @inlineCallbacks
    def test_create_receiverfiles(self):

        yield self.emulate_file_upload(self.dummySubmission['submission_gus'])
        yield self._force_finalize(self.dummySubmission['submission_gus'])

        # create receivertip its NEEDED to create receiverfile
        self.rt = yield delivery_sched.tip_creation()
        self.assertTrue(isinstance(self.rt, list))

        self.rfileslist = yield delivery_sched.receiverfile_planning()
        # return a list of lists [ "file_id", status, "f_path", len, "receiver_desc" ]
        self.assertTrue(isinstance(self.rfileslist, list))

        for (fid, status, fpath, flen, receiver_desc) in self.rfileslist:

            rfdesc = yield delivery_sched.receiverfile_create(fid,
                                    status, fpath, flen, receiver_desc)
            self.assertEqual(rfdesc['mark'], u'not notified')
            self.assertEqual(rfdesc['receiver_id'], receiver_desc['receiver_gus'])
            self.assertEqual(rfdesc['internalfile_id'], fid)

        self.fil = yield delivery_sched.get_files_by_itip(self.dummySubmission['submission_gus'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 2)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.dummySubmission['submission_gus'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 2)
        self.assertEqual(self.rfi[0]['mark'], u'not notified')
        self.assertEqual(self.rfi[1]['mark'], u'not notified')
        self.assertEqual(self.rfi[0]['status'], u'reference')
        self.assertEqual(self.rfi[1]['status'], u'reference')

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['submission_gus'])
        self.assertEqual(len(self.wbfls), 2)
        self.assertEqual(self.wbfls[0]['sha2sum'], self.fil[0]['sha2sum'])
        self.assertEqual(self.wbfls[1]['sha2sum'], self.fil[1]['sha2sum'])

    @inlineCallbacks
    def test_access_from_receipt(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['submission_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        # In the WB/Receiver Tip interface, wb_fields are called fields.
        # This can be uniformed when API would be cleaned of the _gus
        self.assertTrue(wb_tip.has_key('fields'))

    def get_new_receiver_desc(self, descpattern):
        new_r = dict(self.dummyReceiver)
        new_r['name'] = new_r['username'] =\
        new_r['mail_address'] = unicode("%s@%s.xxx" % (descpattern, descpattern))
        new_r['password'] = helpers.VALID_PASSWORD1
        # localized dict required in desc
        new_r['description'] =  "am I ignored ? %s" % descpattern 
        return new_r

    @inlineCallbacks
    def test_submission_with_receiver_selection(self):

        yield create_receiver(self.get_new_receiver_desc("second"))
        yield create_receiver(self.get_new_receiver_desc("third"))
        yield create_receiver(self.get_new_receiver_desc("fourth"))

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        self.assertEqual(len(self.receivers), 4)

        self.dummyContext['receivers'] = [ self.receivers[0]['receiver_gus'],
                                           self.receivers[1]['receiver_gus'],
                                           self.receivers[2]['receiver_gus'],
                                           self.receivers[3]['receiver_gus'] ]
        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        for attrname in models.Context.localized_strings:
            self.dummyContext[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        context_status = yield update_context(self.dummyContext['context_gus'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= dict(self.dummySubmission)
        # submission_request['context_gus'] = context_status['context_gus']
        submission_request['submission_gus'] = submission_request['id'] = ''
        submission_request['finalize'] = False
        submission_request['receivers'] = [ self.receivers[0]['receiver_gus'],
                                            self.receivers[1]['receiver_gus'],
                                            self.receivers[2]['receiver_gus'] ]

        status = yield submission.create_submission(submission_request, finalize=False)
        just_empty_eventually_internaltip = yield delivery_sched.tip_creation()

        # Checks, the submission need to be the same now
        self.assertEqual(len(submission_request['receivers']), len(status['receivers']))

        status['finalize'] = True
        submission_request['context_gus'] = context_status['context_gus'] # reused
        status['receivers'] = [ self.receivers[0]['receiver_gus'],
                                self.receivers[3]['receiver_gus'] ]

        status = yield submission.update_submission(status['submission_gus'], status, finalize=True)

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(status['receivers']))


    @inlineCallbacks
    def test_update_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        submission_desc['context_gus'] = self.dummyContext['context_gus']
        submission_desc['submission_gus'] = submission_desc['id'] = submission_desc['mark'] = None

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['wb_fields'] = helpers.fill_random_fields(self.dummyContext)
        status['finalize'] = True

        status = yield submission.update_submission(status['submission_gus'], status, finalize=True)

        receipt = yield submission.create_whistleblower_tip(status)
        wb_access_id = yield authentication.login_wb(receipt)

        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        self.assertTrue(wb_tip.has_key('fields'))


    @inlineCallbacks
    def test_unable_to_access_finalized(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        submission_desc['context_gus'] = self.dummyContext['context_gus']

        status = yield submission.create_submission(submission_desc, finalize=True)
        try:
            yield submission.update_submission(status['submission_gus'], status, finalize=True)
        except errors.SubmissionConcluded:
            self.assertTrue(True)
            return
        self.assertTrue(False)


    @inlineCallbacks
    def test_fields_validator_all_fields(self):

        sbmt = dict(self.dummySubmission)

        sbmt['wb_fields'] = {}
        for sf in self.dummyContext['fields']:

            if sf['type'] != u"text":
                assert self['type'] == u'text', \
                    "Dummy fields had only 'text' when this test has been dev"

            sbmt['wb_fields'].update({ sf['key'] : "something" })

        try:
            status = yield submission.create_submission(sbmt, finalize=True)
            self.assertEqual(status['wb_fields'], sbmt['wb_fields'] )
        except Exception as excep:
            print "Unexpected error: %s", excep
            self.assertTrue(False)

    @inlineCallbacks
    def test_fields_fail_unexpected_presence(self):

        sbmt = helpers.get_dummy_submission(self.dummySubmission['context_gus'], self.dummyContext['fields'])
        sbmt['wb_fields'].update({ 'alien' : 'predator' })

        try:
            yield submission.create_submission(sbmt, finalize=True)
            self.assertTrue(False)
        except Exception as excep:
            self.assertEqual(excep.reason,
                             u"Submission do not validate the input fields [Submitted field 'alien' not expected in context]")

    @inlineCallbacks
    def test_fields_fail_missing_required(self):

        required_key = self.dummyContext['fields'][0]['key']
        sbmt = helpers.get_dummy_submission(self.dummySubmission['context_gus'], self.dummyContext['fields'])
        del sbmt['wb_fields'][required_key]

        try:
            yield submission.create_submission(sbmt, finalize=True)
            self.assertTrue(False)
        except Exception as excep:
            self.assertTrue(excep.reason.startswith(u"Submission do not validate the input fields [Missing field"))

    def download_token_test(self, id_val, id_type):
         # test token generation
         d = DownloadToken(id_val, id_type)
         self.assertNotEqual(d.id, None)

         # test token use during token validity
         (id_val_check, id_type_check) = DownloadToken.get(d.id)
         self.assertEqual(id_val_check, id_val)
         self.assertEqual(id_type_check, id_type)

         # emulate reactor.callLater on Download Token
         d.expire()

         # test token use after token validity;
         # n.b. this is equal of testing not existent token
         (id_val_check, id_type_check) = DownloadToken.get(d.id)
         self.assertEqual(id_val_check, None)
         self.assertEqual(id_type_check, None)

    @inlineCallbacks
    def test_download_tokens(self):

         yield self.test_create_receiverfiles()

         # Test Download Token Creation/Access for rtip
         for rtip in self.rt:
             self.download_token_test(rtip, 'rtip')

         # Test Download Token Creation/Access for rfile
         for rfile in self.rfi:
             self.download_token_test(rfile['id'], 'rfile')

