# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import os
import re

import tarfile
import StringIO

from twisted.internet.defer import inlineCallbacks

# override GLSetting
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, submission, wbtip
from globaleaks.handlers.admin import create_context, update_context, create_receiver, get_receiver_list
from globaleaks.handlers.receiver import get_receiver_tip_list
from globaleaks.handlers.files import download_all_files, serialize_receiver_file
from globaleaks.handlers.collection import get_compression_opts, CollectionStreamer
from globaleaks.rest import errors
from globaleaks.models import InternalTip
from globaleaks.utils.zipstream import ZipStream, ZIP_STORED, ZIP_DEFLATED

@transact_ro
def collect_ifile_as_wb_without_wbtip(store, internaltip_id):
    file_list = []
    itip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    for internalfile in itip.internalfiles:
        file_list.append(wbtip.wb_serialize_file(internalfile))
    return file_list

class TestSubmission(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def test_001_create_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        self.assertEqual(status['mark'], u'submission')

    @inlineCallbacks
    def test_002_fail_submission_missing_required_file(self):
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
    def test_003_create_submission_attach_files_finalize_and_access_wbtip(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        yield self.emulate_file_upload(self.dummySubmission['id'])

        status = yield submission.update_submission(status['id'], status, finalize=True)

        self.assertEqual(status['mark'], u'finalize')

        receipt = yield submission.create_whistleblower_tip(status)

        self.assertTrue(re.match(self.dummyNode['receipt_regexp'], receipt))

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        # In the WB/Receiver Tip interface, wb_fields are called fields.
        # This can be uniformed when API would be cleaned of the _id
        self.assertTrue(wb_tip.has_key('fields'))

    @inlineCallbacks
    def test_004_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):

        yield self.test_003_create_submission_attach_files_finalize_and_access_wbtip()

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
        self.assertEqual(len(self.fil), 4)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 8)

        for i in range(0, 8):
            self.assertTrue(self.rfi[i]['mark'] in [u'not notified', u'skipped'])
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'nokey'])

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['id'])
        self.assertEqual(len(self.wbfls), 4)

    @inlineCallbacks
    def test_005_create_receiverfiles_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        yield self.test_003_create_submission_attach_files_finalize_and_access_wbtip()

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
        self.assertEqual(len(self.fil), 4)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.dummySubmission['id'])
        self.assertTrue(isinstance(self.rfi, list))

        self.assertEqual(len(self.rfi), 8)
        # no rfiles are created for the receivers that have no key
        for i in range(0, 8):
            self.assertTrue(self.rfi[i]['mark'] in [u'not notified', u'skipped'])
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'nokey'])

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['id'])
        self.assertEqual(len(self.wbfls), 4)

    @inlineCallbacks
    def test_007_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        rcvrs_ids = []

        for rcvr in self.receivers:
            rcvrs_ids.append(rcvr['id'])

        self.dummyContext['receivers'] = rcvrs_ids
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

        submission_request['receivers'] = rcvrs_ids

        status = yield submission.create_submission(submission_request, finalize=False)
        just_empty_eventually_internaltip = yield delivery_sched.tip_creation()

        # Checks, the submission need to be the same now
        self.assertEqual(len(submission_request['receivers']), len(status['receivers']))

        status['finalize'] = True
        submission_request['context_id'] = context_status['id'] # reused
        status['receivers'] = rcvrs_ids

        status = yield submission.update_submission(status['id'], status, finalize=True)

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(status['receivers']))


    @inlineCallbacks
    def test_008_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        rcvrs_ids = []

        for rcvr in self.receivers:
            rcvrs_ids.append(rcvr['id'])

        self.dummyContext['receivers'] = rcvrs_ids
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
        submission_request['receivers'] = rcvrs_ids

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True), errors.SubmissionFailFields)

    @inlineCallbacks
    def test_009_update_submission(self):
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
    def test_010_unable_to_access_finalized(self):
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
    def test_011_fields_validator_all_fields(self):

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
    def test_012_fields_fail_unexpected_presence(self):

        sbmt = self.get_dummy_submission(self.dummyContext['id'], self.dummyContext['fields'])
        sbmt['wb_fields'].update({ 'alien' : 'predator' })

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)

    @inlineCallbacks
    def test_013_fields_fail_missing_required(self):

        required_key = self.dummyContext['fields'][0]['key']
        sbmt = self.get_dummy_submission(self.dummyContext['id'], self.dummyContext['fields'])
        del sbmt['wb_fields'][required_key]

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)
