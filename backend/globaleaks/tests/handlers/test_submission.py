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
from globaleaks.handlers.admin import update_context, get_receiver_list
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
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        self.assertEqual(self.submission_desc['mark'], u'submission')

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['finalize'] = True

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        yield self.emulate_file_upload(self.submission_desc['id'])

        self.submission_desc = yield submission.update_submission(self.submission_desc['id'], self.submission_desc, True, 'en')

        self.assertEqual(self.submission_desc['mark'], u'finalize')

        receipt = yield submission.create_whistleblower_tip(self.submission_desc)

        self.assertTrue(re.match(GLSetting.defaults.receipt_regexp, receipt))

        wb_access_id = yield authentication.login_wb(receipt)

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('wb_steps' in wb_tip)

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

        self.fil = yield delivery_sched.get_files_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 2)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 4)

        for i in range(0, 4):
            self.assertTrue(self.rfi[i]['mark'] in [u'not notified', u'skipped'])
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'encrypted'])

        # verify the checksum returned by whistleblower POV, I'm not using
        #  wfv = yield tip.get_files_wb()
        # because is not generated a WhistleblowerTip in this test
        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.submission_desc['id'])
        self.assertEqual(len(self.wbfls), 2)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):

        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['finalize'] = True

        self.submission_desc = yield submission.create_submission(self.submission_desc, True, 'en')

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(self.submission_desc['receivers']))


    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        # Create a new request with selected three of the four receivers
        submission_request = yield self.get_dummy_submission(self.dummyContext['id'])

        yield self.assertFailure(submission.create_submission(submission_request, True, 'en'),
                                 errors.SubmissionFailFields)

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        self.submission_desc['wb_steps'] = yield helpers.fill_random_fields(self.dummyContext['id'])
        self.submission_desc['finalize'] = True

        self.submission_desc = yield submission.update_submission(self.submission_desc['id'], self.submission_desc, True, 'en')

        receipt = yield submission.create_whistleblower_tip(self.submission_desc)
        wb_access_id = yield authentication.login_wb(receipt)

        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('wb_steps' in wb_tip)

    @inlineCallbacks
    def test_unable_to_update_finalized(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['finalize'] = True

        self.submission_desc = yield submission.create_submission(self.submission_desc, True, 'en')
        try:
            yield submission.update_submission(self.submission_desc['id'], self.submission_desc, True, 'en')
        except errors.SubmissionConcluded:
            self.assertTrue(True)
            return
        self.assertTrue(False)

    @inlineCallbacks
    def test_fields_fail_unexpected_presence(self):

        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        found_at_least_a_field = False

        for s in self.submission_desc['wb_steps']:
            for f in s['children']:
                # we assign a random id to the first field
                f['id'] = 'alien'
                found_at_least_a_field = True
                break

        self.assertTrue(found_at_least_a_field)

        yield self.assertFailure(submission.create_submission(self.submission_desc, True, 'en'),
                                 errors.SubmissionFailFields)

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

        yield self.assertFailure(submission.create_submission(sbmt, True, 'en'),
                                 errors.SubmissionFailFields)

class Test_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionCreate

    @inlineCallbacks
    def test_post(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        handler = self.request(self.submission_desc, {})
        yield handler.post()

        self.submission_desc = self.responses[0]

        self.responses = []

        yield self.emulate_file_upload(self.submission_desc['id'])

        self.submission_desc['finalize'] = True

        handler = self.request(self.submission_desc, {})
        yield handler.post()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)


class Test_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionInstance

    def test_get_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.get("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_get_existent_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            yield handler.get(submission_id)
            self.assertTrue(isinstance(self.responses, list))
            self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)

    @inlineCallbacks
    def test_put_with_finalize_false(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        self.submission_desc['finalize'] = False

        handler = self.request({}, body=json.dumps(self.submission_desc))
        yield handler.put(self.submission_desc['id'])

        self.assertEqual(self.responses[0]['receipt'], '')

    @inlineCallbacks
    def test_put_with_finalize_true(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        self.submission_desc['finalize'] = True

        handler = self.request({}, body=json.dumps(self.submission_desc))
        yield handler.put(self.submission_desc['id'])

        self.assertNotEqual(self.responses[0]['receipt'], '')

    def test_delete_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.delete("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_delete_submission_not_finalized(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield submission.create_submission(self.submission_desc, False, 'en')

        handler = self.request({})
        yield handler.delete(self.submission_desc['id'])

    @inlineCallbacks
    def test_delete_existent_but_finalized_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            self.assertFailure(handler.delete(submission_id), errors.SubmissionConcluded)
