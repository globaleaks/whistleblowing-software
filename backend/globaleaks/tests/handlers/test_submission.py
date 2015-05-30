# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from twisted.internet.defer import inlineCallbacks, returnValue

# override GLSetting
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.tests import helpers
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.admin import create_receiver
from globaleaks.rest import errors
from globaleaks.models import InternalTip
from globaleaks.utils.token import Token
from globaleaks.handlers.submission import create_whistleblower_tip, SubmissionCreate, SubmissionInstance

# and here, our protagonist character:
from globaleaks.handlers.submission import create_submission

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
    def create_submission(self, request):
        token = Token('submission', request['context_id'])
        output = yield create_submission(token, request, 'en')
        returnValue(output)

    @inlineCallbacks
    def create_submission_with_files(self, request):
        token = Token('submission', request['context_id'])
        yield self.emulate_file_upload(token, 3)
        output = yield create_submission(token, request, 'en')
        returnValue(output)

    @inlineCallbacks
    def test_create_submission_valid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_create_submission_invalid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        for wb_step in self.submission_desc['wb_steps']:
            for c in wb_step['children']:
                c['value'] = unicode("You know nothing John Snow" * 100  * 100)

        yield self.assertFailure(self.create_submission(self.submission_desc),
                                 errors.InvalidInputFormat)

    @inlineCallbacks
    def test_create_submission_with_wrong_receiver(self):
        disassociated_receiver = yield create_receiver(self.get_dummy_receiver('dumb'), 'en')
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['receivers'].append(disassociated_receiver['id'])
        yield self.assertFailure(self.create_submission(self.submission_desc),
                                 errors.InvalidInputFormat)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission_with_files(self.submission_desc)

        wb_access_id, _, _ = yield authentication.login_wb(self.submission_desc['receipt'])

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('wb_steps' in wb_tip)

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):
        yield self.test_create_submission_attach_files_finalize_and_access_wbtip()

        self.rfilesdict = yield delivery_sched.receiverfile_planning()
        # return a list of lists [ "file_id", status, "f_path", len, "receiver_desc" ]
        self.assertTrue(isinstance(self.rfilesdict, dict))

        for ifile_path, receivermap in self.rfilesdict.iteritems():
            yield delivery_sched.encrypt_where_available(receivermap)
            for elem in receivermap:
                yield delivery_sched.receiverfile_create(ifile_path,
                                                         elem['path'],
                                                         elem['status'],
                                                         elem['size'],
                                                         elem['receiver'])

        self.fil = yield delivery_sched.get_files_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 3)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 6)

        for i in range(0, 6):
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'encrypted'])

        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.submission_desc['id'])
        self.assertEqual(len(self.wbfls), 3)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):
        GLSetting.memory_copy.allow_unencrypted = False

        # Create a new request with selected three of the four receivers
        submission_request = yield self.get_dummy_submission(self.dummyContext['id'])

        yield self.assertFailure(self.create_submission(submission_request),
                                 errors.SubmissionFailFields)

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['wb_steps'] = yield self.fill_random_fields(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

        wb_access_id, _, _ = yield authentication.login_wb(self.submission_desc['receipt'])

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

        yield self.assertFailure(self.create_submission(self.submission_desc),
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

        yield self.assertFailure(self.create_submission(sbmt),
                                 errors.SubmissionFailFields)

class Test_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionCreate

    @inlineCallbacks
    def test_post(self):
        handler = self.request(
            {
              'context_id': self.dummyContext['id'],
              'receivers': [],
              'wb_steps': [],
              'human_captcha_answer': 0
            }
        )
        yield handler.post()


class Test_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    @inlineCallbacks
    def test_put(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        token = Token('submission', self.dummyContext['id'])

        handler = self.request(self.submission_desc)
        yield handler.put(token.token_id)
