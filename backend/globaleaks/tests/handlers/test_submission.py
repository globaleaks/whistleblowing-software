# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import json
import re

from twisted.internet.defer import inlineCallbacks, returnValue

# override GLSetting
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.tests import helpers
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.admin import create_receiver
from globaleaks.rest import requests, errors
from globaleaks.models import InternalTip
from globaleaks.utils.token import Token
from globaleaks.handlers.submission import create_whistleblower_tip, SubmissionCreate, SubmissionInstance

# and here, our protagonist character:
from globaleaks.handlers.submission import db_finalize_submission

# necessary because Token is a TempObj -- but I've not understand exactly the logic
import globaleaks.utils.token.reactor
from twisted.internet import task
globaleaks.utils.token.reactor = task.Clock()

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
    def create_submisstest(self, request):

        token = Token('submission', request['context_id'], debug=False)
        output = yield db_finalize_submission(token, request, 'en')
        returnValue(output)

    @inlineCallbacks
    def test_create_submission_valid_submission_finalized(self):

        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = self.create_submisstest(self.submission_desc)
        print self.submission_desc

    @inlineCallbacks
    def test_create_submission_valid_submission_finalize_by_update(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submisstest(self.submission_desc)

        self.assertEqual(self.submission_desc['mark'], u'finalize')

    @inlineCallbacks
    def test_create_submission_valid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc = yield self.create_submisstest(self.submission_desc)

        self.assertEqual(self.submission_desc['mark'], u'submission')

        for wb_step in self.submission_desc['wb_steps']:
            for c in wb_step['children']:
                c['value'] = unicode("You know nothing John Snow" * 100  * 100)

        self.submission_desc['finalize'] = True

        yield self.assertFailure(self.create_submisstest(self.submission_desc),
                                 errors.InvalidInputFormat )

    @inlineCallbacks
    def test_create_submission_with_wrong_receiver(self):
        disassociated_receiver = yield create_receiver(self.get_dummy_receiver('dumb'), 'en')
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['receivers'].append(disassociated_receiver['id'])
        yield self.assertFailure(self.create_submisstest(self.submission_desc),
                                 errors.InvalidInputFormat)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['finalize'] = True

        token = Token('submission', self.submission_desc['context_id'])
        self.submission_desc = yield self.create_submisstest(self.submission_desc)

        x = yield self.emulate_file_upload(token)
        print "check ABC", x

        receipt = yield create_whistleblower_tip(self.submission_desc)

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

        self.submission_desc = yield self.create_submisstest(self.submission_desc)

        receiver_tips = yield delivery_sched.tip_creation()
        self.assertEqual(len(receiver_tips), len(self.submission_desc['receivers']))


    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):

        GLSetting.memory_copy.allow_unencrypted = False

        # Create a new request with selected three of the four receivers
        submission_request = yield self.get_dummy_submission(self.dummyContext['id'])

        yield self.assertFailure(self.create_submisstest(submission_request),
                                 errors.SubmissionFailFields)

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['wb_steps'] = yield helpers.fill_random_fields(self.dummyContext['id'])
        self.submission_desc = yield self.create_submisstest(self.submission_desc)

        receipt = yield create_whistleblower_tip(self.submission_desc)
        wb_access_id = yield authentication.login_wb(receipt)

        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('wb_steps' in wb_tip)


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

        yield self.assertFailure(self.create_submisstest(self.submission_desc),
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

        yield self.assertFailure(self.create_submisstest(sbmt),
                                 errors.SubmissionFailFields)

class Test_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionCreate

    @inlineCallbacks
    def test_post(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        handler = self.request(self.submission_desc, {})
        yield handler.post()

        self.submission_desc = self.responses[0]

        self.responses = []
        token = Token('submission', self.submission_desc['context_id'])

        yield self.emulate_file_upload(token)

        self.submission_desc['finalize'] = True

        handler = self.request(self.submission_desc, {'context_id': 123})
        yield handler.post()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)


class Test_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

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
    def test_delete_existent_but_finalized_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            self.assertFailure(handler.delete(submission_id), errors.SubmissionConcluded)
