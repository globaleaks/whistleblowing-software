# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import re
import StringIO
import tarfile

from twisted.internet.defer import inlineCallbacks

# override GLSetting
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, submission, wbtip
from globaleaks.handlers.admin import create_context, update_context, create_receiver, get_receiver_list
from globaleaks.rest import requests, errors
from globaleaks.models import InternalTip


@transact_ro
def collect_ifile_as_wb_without_wbtip(store, internaltip_id):
    file_list = []
    itip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    for internalfile in itip.internalfiles:
        file_list.append(wbtip.wb_serialize_file(internalfile))
    return file_list

class TestSubmission(helpers.TestGLWithPopulatedDB):

    encryption_scenario = 'ALL_PLAINTEXT'

    @inlineCallbacks
    def test_create_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        self.assertEqual(status['mark'], u'submission')

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = True
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        yield self.emulate_file_upload(self.dummySubmission['id'])

        status = yield submission.update_submission(status['id'], status, finalize=True)

        self.assertEqual(status['mark'], u'finalize')

        receipt = yield submission.create_whistleblower_tip(status)

        self.assertTrue(re.match(GLSetting.defaults.receipt_regexp, receipt))

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        self.assertTrue(wb_tip.has_key('wb_steps'))

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):

        yield self.test_create_submission_attach_files_finalize_and_access_wbtip()

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
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'encrypted'])

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.dummySubmission['id'])
        self.assertEqual(len(self.wbfls), 4)

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        yield self.test_create_submission_attach_files_finalize_and_access_wbtip()

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
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        rcvrs_ids = []

        for rcvr in self.receivers:
            rcvrs_ids.append(rcvr['id'])

        self.dummyContext['receivers'] = rcvrs_ids
        self.dummyContext['selectable_receiver'] = True

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
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        # for some reason, the first receiver is no more with the same ID
        self.receivers = yield get_receiver_list()

        rcvrs_ids = []

        for rcvr in self.receivers:
            rcvrs_ids.append(rcvr['id'])

        self.dummyContext['receivers'] = rcvrs_ids
        self.dummyContext['selectable_receiver'] = True

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
    def test_update_submission(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        submission_desc['context_id'] = self.dummyContext['id']
        submission_desc['id'] = submission_desc['mark'] = None

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['wb_steps'] = yield helpers.fill_random_fields(self.dummyContext['id'])
        status['finalize'] = True

        status = yield submission.update_submission(status['id'], status, finalize=True)

        receipt = yield submission.create_whistleblower_tip(status)
        wb_access_id = yield authentication.login_wb(receipt)

        wb_tip = yield wbtip.get_internaltip_wb(wb_access_id)

        self.assertTrue(wb_tip.has_key('wb_steps'))

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
    def test_fields_fail_unexpected_presence(self):

        sbmt = yield self.get_dummy_submission(self.dummyContext['id'])

        found_at_least_a_field = False

        for s in sbmt['wb_steps']:
            for f in s['children']:
                # we assign a random id to the first field
                f['id'] = 'alien'
                found_at_least_a_field = True
                break

        self.assertTrue(found_at_least_a_field)

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)

    @inlineCallbacks
    def test_fields_fail_missing_required(self):

        required_key = unicode(self.dummyFields[0]['id']) # first of the dummy field is
                                                          # marked as required!

        sbmt = yield self.get_dummy_submission(self.dummyContext['id'])
        i = 0
        done = False
        for s in sbmt['wb_steps']:
            for f in s['children']:
                if f['id'] == required_key:
                    s['children'].pop(i)
                    done = True
                    break
            if done:
                break
            i += 1

        yield self.assertFailure(submission.create_submission(sbmt, finalize=True), errors.SubmissionFailFields)

class Test_001_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionCreate

    @inlineCallbacks
    def test_001_post(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False

        handler = self.request(submission_desc, {})
        yield handler.post()

        submission_desc = self.responses[0]

        self.responses = []

        yield self.emulate_file_upload(submission_desc['id'])

        submission_desc['finalize'] = True

        handler = self.request(submission_desc, {})
        yield handler.post()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)


class Test_002_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionInstance

    def test_001_get_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.get("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_002_get_existent_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            yield handler.get(submission_id)
            self.assertTrue(isinstance(self.responses, list))
            self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)

    @inlineCallbacks
    def test_003_put_with_finalize_false(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['finalize'] = False

        handler = self.request({}, body=json.dumps(status))
        yield handler.put(status['id'])

        self.assertEqual(self.responses[0]['receipt'], '')

    @inlineCallbacks
    def test_004_put_with_finalize_true(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['finalize'] = True

        handler = self.request({}, body=json.dumps(status))
        yield handler.put(status['id'])

        self.assertNotEqual(self.responses[0]['receipt'], '')

    def test_005_delete_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.delete("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_006_delete_submission_not_finalized(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        handler = self.request({})
        yield handler.delete(status['id'])

    @inlineCallbacks
    def test_007_delete_existent_but_finalized_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            self.assertFailure(handler.delete(submission_id), errors.SubmissionConcluded)
