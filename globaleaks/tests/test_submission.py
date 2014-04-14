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
from globaleaks.handlers.admin import create_context, update_context, create_receiver, get_receiver_list
from globaleaks.rest import errors
from globaleaks.models import InternalTip
from globaleaks.security import GLSecureTemporaryFile

@transact_ro
def collect_ifile_as_wb_without_wbtip(store, internaltip_id):
    file_list = []
    itip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    for internalfile in itip.internalfiles:
        file_list.append(wbtip.wb_serialize_file(internalfile))
    return file_list


class TestSubmission(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)

	temporary_file1 = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        temporary_file1.write("ANTANI")
        temporary_file1.avoid_delete()

        temporary_file2 = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        temporary_file2.write("ANTANIANTANIANTANI")
        temporary_file2.avoid_delete()

        self.dummyFile1 = {
            'body': temporary_file1,
            'body_len': len("ANTANI"),
            'body_filepath': temporary_file1.filepath,
            'filename': ''.join(unichr(x) for x in range(0x400, 0x40A)),
            'content_type': 'application/octect',
        }

        self.dummyFile2 = {
            'body': temporary_file2,
            'body_len': len("ANTANIANTANIANTANI"),
            'body_filepath': temporary_file2.filepath,
            'filename': ''.join(unichr(x) for x in range(0x400, 0x40A)),
            'content_type': 'application/octect',
        }

    # --------------------------------------------------------- #
    @inlineCallbacks
    def test_create_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        retval = re.match(self.dummyNode['receipt_regexp'], receipt)
        self.assertTrue(retval)

    @inlineCallbacks
    def test_fail_submission_missing_file(self):

        mycopy = dict(self.dummyContext)
        mycopy['file_required'] = True
        del mycopy['id']

        for attrname in models.Context.localized_strings:
            mycopy[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        context_status = yield create_context(mycopy)
        submission_desc = dict(self.dummySubmission)

        submission_desc['context_id'] = context_status['id']
        submission_desc['finalize'] = True
        submission_desc['wb_fields'] = helpers.fill_random_fields(mycopy)

        yield self.assertFailure(submission.create_submission(submission_desc, finalize=True), errors.FileRequiredMissing)

    @inlineCallbacks
    def emulate_file_upload(self, associated_submission_id):

        relationship1 = yield threads.deferToThread(files.dump_file_fs, self.dummyFile1)
        self.registered_file1 = yield files.register_file_db(
            self.dummyFile1, relationship1, associated_submission_id,
        )

        relationship2 = yield threads.deferToThread(files.dump_file_fs, self.dummyFile2)
        self.registered_file2 = yield files.register_file_db(
            self.dummyFile2, relationship2, associated_submission_id,
            )

    @inlineCallbacks
    def test_pternalfiles(self):
        yield self.emulate_file_upload(self.dummySubmission['id'])
        keydiff = {'size', 'content_type', 'name', 'creation_date', 'id'} - set(self.registered_file1.keys())
        self.assertFalse(keydiff)
        keydiff = {'size', 'content_type', 'name', 'creation_date', 'id'} - set(self.registered_file2.keys())
        self.assertFalse(keydiff)

    @transact
    def _force_finalize(self, store, submission_id):
        it = store.find(models.InternalTip, models.InternalTip.id == submission_id).one()
        it.mark = models.InternalTip._marker[1] # 'finalized'

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):

        yield self.emulate_file_upload(self.dummySubmission['id'])
        yield self._force_finalize(self.dummySubmission['id'])

        # create receivertip its NEEDED to create receiverfile
        self.rt = yield delivery_sched.tip_creation()
        self.assertTrue(isinstance(self.rt, list))

        self.rfilesdict = yield delivery_sched.receiverfile_planning()
        # return a list of lists [ "file_id", status, "f_path", len, "receiver_desc" ]
        self.assertTrue(isinstance(self.rfilesdict, dict))

        for ifile_path, receivermap in self.rfilesdict.iteritems():
            yield delivery_sched.encrypt_where_available(receivermap)
            for elem in receivermap:
                rfdesc = yield delivery_sched.receiverfile_create(ifile_path,
                                    elem['path'], elem['status'], elem['size'], elem['receiver'])
                self.assertEqual(rfdesc['mark'], u'not notified')
                self.assertEqual(rfdesc['receiver_id'], elem['receiver']['id'])

        self.fil = yield delivery_sched.get_files_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 2)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 2)
        self.assertEqual(self.rfi[0]['mark'], u'not notified')
        self.assertEqual(self.rfi[1]['mark'], u'not notified')
        self.assertEqual(self.rfi[0]['status'], u'reference')
        self.assertEqual(self.rfi[1]['status'], u'reference')

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['id'])
        self.assertEqual(len(self.wbfls), 2)

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        yield self.emulate_file_upload(self.dummySubmission['id'])
        yield self._force_finalize(self.dummySubmission['id'])

        # create receivertip its NEEDED to create receiverfile
        self.rt = yield delivery_sched.tip_creation()
        self.assertTrue(isinstance(self.rt, list))

        self.rfilesdict = yield delivery_sched.receiverfile_planning()
        # return a list of lists [ "file_id", status, "f_path", len, "receiver_desc" ]
        self.assertTrue(isinstance(self.rfilesdict, dict))

        for ifile_path, receivermap in self.rfilesdict.iteritems():
            yield delivery_sched.encrypt_where_available(receivermap)
            for elem in receivermap:
                rfdesc = yield delivery_sched.receiverfile_create(ifile_path,
                                    elem['path'], elem['status'], elem['size'], elem['receiver'])
                self.assertEqual(rfdesc['mark'], u'not notified')
                self.assertEqual(rfdesc['receiver_id'], elem['receiver']['id'])

        self.fil = yield delivery_sched.get_files_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 2)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.rfi, list))

        self.assertEqual(len(self.rfi), 2) # no rfiles are created for the receivers that have no key
        self.assertEqual(self.rfi[0]['mark'], u'not notified')
        self.assertEqual(self.rfi[1]['mark'], u'not notified')
        self.assertEqual(self.rfi[0]['status'], u'nokey')
        self.assertEqual(self.rfi[1]['status'], u'nokey')

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['id'])
        self.assertEqual(len(self.wbfls), 2)


    @inlineCallbacks
    def test_access_from_receipt(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=True)
        receipt = yield submission.create_whistleblower_tip(status)

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        # In the WB/Receiver Tip interface, wb_fields are called fields.
        # This can be uniformed when API would be cleaned of the _id
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
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):

        yield create_receiver(self.get_new_receiver_desc("second"))
        yield create_receiver(self.get_new_receiver_desc("third"))
        yield create_receiver(self.get_new_receiver_desc("fourth"))

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        self.assertEqual(len(self.receivers), 4)

        self.dummyContext['receivers'] = [ self.receivers[0]['id'],
                                           self.receivers[1]['id'],
                                           self.receivers[2]['id'],
                                           self.receivers[3]['id'] ]
        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        for attrname in models.Context.localized_strings:
            self.dummyContext[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        context_status = yield update_context(self.dummyContext['id'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= dict(self.dummySubmission)
        # submission_request['context_id'] = context_status['context_id']
        submission_request['id'] = ''
        submission_request['finalize'] = False
        submission_request['receivers'] = [ self.receivers[0]['id'],
                                            self.receivers[1]['id'],
                                            self.receivers[2]['id'] ]

        status = yield submission.create_submission(submission_request, finalize=False)
        just_empty_eventually_internaltip = yield delivery_sched.tip_creation()

        # Checks, the submission need to be the same now
        self.assertEqual(len(submission_request['receivers']), len(status['receivers']))

        status['finalize'] = True
        submission_request['context_id'] = context_status['id'] # reused
        status['receivers'] = [ self.receivers[0]['id'],
                                self.receivers[3]['id'] ]

        status = yield submission.update_submission(status['id'], status, finalize=True)

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(status['receivers']))


    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        yield create_receiver(self.get_new_receiver_desc("second"))
        yield create_receiver(self.get_new_receiver_desc("third"))
        yield create_receiver(self.get_new_receiver_desc("fourth"))

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        self.assertEqual(len(self.receivers), 4)

        self.dummyContext['receivers'] = [ self.receivers[0]['id'],
                                           self.receivers[1]['id'],
                                           self.receivers[2]['id'],
                                           self.receivers[3]['id'] ]
        self.dummyContext['selectable_receiver'] = True
        self.dummyContext['escalation_threshold'] = 0

        for attrname in models.Context.localized_strings:
            self.dummyContext[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        context_status = yield update_context(self.dummyContext['id'], self.dummyContext)

        # Create a new request with selected three of the four receivers
        submission_request= dict(self.dummySubmission)
        # submission_request['context_id'] = context_status['context_id']
        submission_request['id'] = ''
        submission_request['finalize'] = False
        submission_request['receivers'] = [ self.receivers[0]['id'],
                                            self.receivers[1]['id'],
                                            self.receivers[2]['id'] ]

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True), errors.SubmissionFailFields)

    @inlineCallbacks
    def test_update_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        submission_desc['context_id'] = self.dummyContext['id']
        submission_desc['id'] = submission_desc['mark'] = None

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['wb_fields'] = helpers.fill_random_fields(self.dummyContext)
        status['finalize'] = True

        status = yield submission.update_submission(status['id'], status, finalize=True)

        receipt = yield submission.create_whistleblower_tip(status)
        wb_access_id = yield authentication.login_wb(receipt)

        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        self.assertTrue(wb_tip.has_key('fields'))


    @inlineCallbacks
    def test_unable_to_access_finalized(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        submission_desc['context_id'] = self.dummyContext['id']

        status = yield submission.create_submission(submission_desc, finalize=True)
        try:
            yield submission.update_submission(status['id'], status, finalize=True)
        except errors.SubmissionConcluded:
            self.assertTrue(True)
            return
        self.assertTrue(False)


    @inlineCallbacks
    def test_fields_validator_all_fields(self):

        sbmt = dict(self.dummySubmission)

        sbmt['wb_fields'] = {}
        i = 0
        for sf in self.dummyContext['fields']:
            assert (sf['type'] == u'text' or sf['type'] == u'textarea'), \
                    "Dummy fields had only 'text' when this test has been dev"

            sbmt['wb_fields'].update({ sf['key'] : { u'value': "something",
                                                     u'answer_order': i} })

            i += 1

        try:
            status = yield submission.create_submission(sbmt, finalize=True)
            self.assertEqual(status['wb_fields'], sbmt['wb_fields'] )
        except Exception as excep:
            print "Unexpected error: %s", excep
            self.assertTrue(False)

    @inlineCallbacks
    def test_fields_fail_unexpected_presence(self):

        sbmt = helpers.get_dummy_submission(self.dummyContext['id'], self.dummyContext['fields'])
        sbmt['wb_fields'].update({ 'alien' : 'predator' })

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)

    @inlineCallbacks
    def test_fields_fail_missing_required(self):

        required_key = self.dummyContext['fields'][0]['key']
        sbmt = helpers.get_dummy_submission(self.dummyContext['id'], self.dummyContext['fields'])
        del sbmt['wb_fields'][required_key]

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)
