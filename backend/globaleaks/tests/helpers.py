# -*- coding: UTF-8

"""
Utilities and basic TestCases.
"""

import copy
import json
import os
import shutil

from cyclone import httpserver
from cyclone.web import Application
from storm.twisted.testing import FakeThreadPool
from twisted.internet import threads, defer, task
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest
from twisted.test import proto_helpers

import sys
reload(sys)
sys.getdefaultencoding()


from globaleaks import db, models, security, event, runner, jobs
from globaleaks.anomaly import Alarm
from globaleaks.db.appdata import load_appdata
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers import authentication, files, rtip, wbtip
from globaleaks.handlers.base import GLHTTPConnection, BaseHandler
from globaleaks.handlers.admin.context import create_context, \
    get_context, update_context, db_get_context_steps
from globaleaks.handlers.admin.receiver import create_receiver
from globaleaks.handlers.admin.field import create_field
from globaleaks.handlers.admin.user import create_admin, create_custodian
from globaleaks.handlers.submission import create_submission, serialize_usertip, \
    serialize_internalfile, serialize_receiverfile
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.security import GLSecureTemporaryFile, generateRandomKey, generateRandomSalt
from globaleaks.utils import tempdict, token, mailutils
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import sum_dicts, datetime_null, datetime_now, log

from . import TEST_DIR

## constants
VALID_PASSWORD1 = u'justapasswordwithaletterandanumberandbiggerthan8chars'
VALID_PASSWORD2 = u'justap455w0rdwithaletterandanumberandbiggerthan8chars'
VALID_SALT1 = security.generateRandomSalt()
VALID_SALT2 = security.generateRandomSalt()
VALID_HASH1 = security.hash_password(VALID_PASSWORD1, VALID_SALT1)
VALID_HASH2 = security.hash_password(VALID_PASSWORD2, VALID_SALT2)
INVALID_PASSWORD = u'antani'

FIXTURES_PATH = os.path.join(TEST_DIR, 'fixtures')

with open(os.path.join(TEST_DIR, 'keys/valid_pgp_key1.txt')) as pgp_file:
    VALID_PGP_KEY1 = unicode(pgp_file.read())

with open(os.path.join(TEST_DIR, 'keys/valid_pgp_key2.txt')) as pgp_file:
    VALID_PGP_KEY2 = unicode(pgp_file.read())

with open(os.path.join(TEST_DIR, 'keys/expired_pgp_key.txt')) as pgp_file:
    EXPIRED_PGP_KEY = unicode(pgp_file.read())

transact.tp = FakeThreadPool()

# client/app/data/fields/whistleblower_identity.json
WHISTLEBLOWER_IDENTITY_FIELD_PATH = \
    os.path.join(GLSettings.client_path,
                 '../../client/app/data/fields/whistleblower_identity.json')

def load_json_file(file_path):
    with open(file_path) as f:
      return json.loads(f.read())

class UTlog:
    @staticmethod
    def err(stuff):
        pass

    @staticmethod
    def debug(stuff):
        pass


log.err = UTlog.err
log.debug = UTlog.debug


def init_glsettings_for_unit_tests():
    GLSettings.testing = True
    GLSettings.set_devel_mode()
    GLSettings.logging = None
    GLSettings.scheduler_threadpool = FakeThreadPool()
    GLSettings.sessions.clear()
    GLSettings.failed_login_attempts = 0
    GLSettings.working_path = './working_path'
    GLSettings.ramdisk_path = os.path.join(GLSettings.working_path, 'ramdisk')

    GLSettings.eval_paths()
    GLSettings.remove_directories()
    GLSettings.create_directories()


def export_fixture(*models):
    """
    Return a valid json object holding all informations handled by the fields.

    :param field: the field we want to export.
    :rtype: str
    :return: a valid JSON string exporting the field.
    """
    return json.dumps([{
        'fields': model.dict(),
        'class': model.__class__.__name__,
    } for model in models], default=str, indent=2)


@transact
def import_fixture(store, fixture):
    """
    Import a valid json object holding all informations, and stores them in the database.

    :return: The traditional deferred used for transaction in GlobaLeaks.
    """
    data = load_json_file(os.path.join(FIXTURES_PATH, fixture))
    for mock in data:
       for k in mock['fields']:
           if k.endswidh('_id') and mock['fields'][k] == '':
               del mock['fields'][k]

       mock_class = getattr(models, mock['class'])
       models.db_forge_obj(store, mock_class, mock['fields'])
       store.commit()


def change_field_type(field, field_type):
    field['instance'] = field_type
    for f in field['children']:
        change_field_type(f, field_type)


def get_file_upload(self):
    return self.request.body

BaseHandler.get_file_upload = get_file_upload


class TestGL(unittest.TestCase):
    initialize_test_database_using_archived_db = True
    encryption_scenario = 'MIXED'  # receivers with pgp and receivers without pgp

    @inlineCallbacks
    def setUp(self):
        self.test_reactor = task.Clock()
        jobs.base.test_reactor = self.test_reactor
        token.TokenList.reactor = self.test_reactor
        runner.test_reactor = self.test_reactor
        tempdict.test_reactor = self.test_reactor
        GLSettings.sessions.reactor = self.test_reactor

        init_glsettings_for_unit_tests()

        self.setUp_dummy()

        if self.initialize_test_database_using_archived_db:
            shutil.copy(
                os.path.join(TEST_DIR, 'db', 'empty', GLSettings.db_file_name),
                os.path.join(GLSettings.working_path, 'db', GLSettings.db_file_name)
            )
        else:
            yield db.init_db()

        yield db.refresh_memory_variables()

        for fixture in getattr(self, 'fixtures', []):
            yield import_fixture(fixture)

        # override of imported memory variables
        GLSettings.memory_copy.allow_unencrypted = True

        Alarm.reset()
        event.EventTrackQueue.reset()
        jobs.statistics_sched.StatisticsSchedule.reset()

        self.internationalized_text = load_appdata()['node']['whistleblowing_button']


    def setUp_dummy(self):
        dummyStuff = MockDict()

        self.dummyFields = dummyStuff.dummyFields
        self.dummyFieldTemplates = dummyStuff.dummyFieldTemplates
        self.dummySteps = dummyStuff.dummySteps
        self.dummyContext = dummyStuff.dummyContext
        self.dummySubmission = dummyStuff.dummySubmission
        self.dummyAdminUser = self.get_dummy_user('admin', 'admin1')
        self.dummyAdminUser['deletable'] = False
        self.dummyCustodianUser = self.get_dummy_user('custodian', 'custodian1')
        self.dummyReceiverUser_1 = self.get_dummy_user('receiver', 'receiver1')
        self.dummyReceiverUser_2 = self.get_dummy_user('receiver', 'receiver2')
        self.dummyReceiver_1 = self.get_dummy_receiver('receiver1')  # the one without PGP
        self.dummyReceiver_2 = self.get_dummy_receiver('receiver2')  # the one with PGP

        if self.encryption_scenario == 'MIXED':
            self.dummyReceiver_1['pgp_key_public'] = ''
            self.dummyReceiver_2['pgp_key_public'] = VALID_PGP_KEY1
        elif self.encryption_scenario == 'ALL_ENCRYPTED':
            self.dummyReceiver_1['pgp_key_public'] = VALID_PGP_KEY1
            self.dummyReceiverUser_2['pgp_key_public'] = VALID_PGP_KEY2
        elif self.encryption_scenario == 'ONE_VALID_ONE_EXPIRED':
            self.dummyReceiver_1['pgp_key_public'] = VALID_PGP_KEY1
            self.dummyReceiver_2['pgp_key_public'] = EXPIRED_PGP_KEY
        elif self.encryption_scenario == 'ALL_PLAINTEXT':
            self.dummyReceiver_1['pgp_key_public'] = ''
            self.dummyReceiver_2['pgp_key_public'] = ''

        self.dummyNode = dummyStuff.dummyNode

        self.assertEqual(os.listdir(GLSettings.submission_path), [])
        self.assertEqual(os.listdir(GLSettings.tmp_upload_path), [])

    def localization_set(self, dict_l, dict_c, language):
        ret = dict(dict_l)

        for attr in getattr(dict_c, 'localized_keys'):
            ret[attr] = {}
            ret[attr][language] = unicode(dict_l[attr])

        return ret

    def get_dummy_user(self, role, descpattern):
        new_u = dict(MockDict().dummyUser)
        new_u['role'] = role
        new_u['username'] = new_u['name'] = new_u['mail_address'] = \
            unicode("%s@%s.xxx" % (descpattern, descpattern))
        new_u['description'] = u""
        new_u['password'] = VALID_PASSWORD1
        new_u['state'] = u'enabled'
        new_u['deletable'] = True

        return new_u

    def get_dummy_receiver(self, descpattern):
        new_u = self.get_dummy_user('receiver', descpattern)
        new_r = dict(MockDict().dummyReceiver)

        return sum_dicts(new_r, new_u)

    def get_dummy_field(self):
        return {
            'id': '',
            'key': '',
            'instance': 'instance',
            'editable': True,
            'template_id': '',
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'antani',
            'type': u'inputbox',
            'preview': False,
            'description': u"field description",
            'hint': u'field hint',
            'multi_entry': False,
            'multi_entry_hint': '',
            'stats_enabled': False,
            'required': False,
            'attrs': {},
            'options': [],
            'children': [],
            'y': 1,
            'x': 1,
            'width': 0 
        }

    @transact
    def create_dummy_field(self, store, **custom_attrs):
        field = self.get_dummy_field()

        fill_localized_keys(field, models.Field.localized_keys, 'en')

        field.update(custom_attrs)

        return models.Field.new(store, field).id

    def fill_random_field_recursively(self, answers, field, value=None):
        # FIXME: currently the function consider:
        # - only first level of fields
        # - all fields are considered as inputboxes
        if value is None:
            value = unicode(''.join(unichr(x) for x in range(0x400, 0x4FF)))
        else:
            value = unicode(value)

        answers[field['id']] = [{'value': value}]

    @transact
    def fill_random_answers(self, store, context_id, value=None):
        """
        return randomly populated contexts associated to specified context
        """
        answers = {}

        steps = db_get_context_steps(store, context_id, 'en')

        for step in steps:
            for field in step['children']:
                self.fill_random_field_recursively(answers, field)

        return answers

    @defer.inlineCallbacks
    def get_dummy_submission(self, context_id):
        """
        this may works until the content of the fields do not start to be validated. like
        numbers shall contain only number, and not URL.
        This validation would not be implemented in validate_jmessage but in structures.Fields

        need to be enhanced generating appropriate data based on the fields.type
        """
        defer.returnValue({
            'context_id': context_id,
            'receivers': (yield get_context(context_id, 'en'))['receivers'],
            'files': [],
            'human_captcha_answer': 0,
            'graph_captcha_answer': '',
            'proof_of_work_answer': 0,
            'identity_provided': False,
            'answers': (yield self.fill_random_answers(context_id))
        })

    def get_dummy_file(self, filename=None, content_type=None, content=None):
        if filename is None:
            filename = ''.join(unichr(x) for x in range(0x400, 0x40A))

        if content_type is None:
            content_type = 'application/octet'

        if content is None:
            content = ''.join(unichr(x) for x in range(0x400, 0x40A))

        temporary_file = GLSecureTemporaryFile(GLSettings.tmp_upload_path)

        temporary_file.write(content)
        temporary_file.avoid_delete()

        return {
            'body': temporary_file,
            'body_len': len(content),
            'body_filepath': temporary_file.filepath,
            'filename': filename,
            'content_type': content_type,
            'submission': False
        }

    def get_dummy_shorturl(self, x = ''):
        return {
          'shorturl': '/s/shorturl' + str(x),
          'longurl': '/longurl' + str(x)
        }

    @inlineCallbacks
    def emulate_file_upload(self, token, n):
        """
        This emulate the file upload of a incomplete submission
        """
        for i in range(0, n):
            dummyFile = self.get_dummy_file()

            dummyFile = yield threads.deferToThread(files.dump_file_fs, dummyFile)
            dummyFile['creation_date'] = datetime_null()

            f = files.serialize_memory_file(dummyFile)

            token.associate_file(dummyFile)

            self.assertFalse({'size', 'content_type', 'name', 'creation_date'} - set(f.keys()))

    @inlineCallbacks
    def emulate_file_append(self, rtip_id, n):
        @transact_ro
        def get_itip_id_from_rtip_id(store, rtip_id):
            return store.find(models.ReceiverTip, models.ReceiverTip.id == rtip_id).one().internaltip_id

        itip_id = yield get_itip_id_from_rtip_id(rtip_id)

        for i in range(0, n):
            dummyFile = self.get_dummy_file()
            dummyFile['submission'] = True

            dummyFile = yield threads.deferToThread(files.dump_file_fs, dummyFile)
            registered_file = yield files.register_file_db(
                dummyFile, itip_id,
            )

            self.assertFalse({'size', 'content_type', 'name', 'creation_date'} - set(registered_file.keys()))

    @transact_ro
    def _exists(self, store, model, *id_args, **id_kwargs):
        if not id_args and not id_kwargs:
            raise ValueError
        return model.get(store, *id_args, **id_kwargs) is not None

    @inlineCallbacks
    def assert_model_exists(self, model, *id_args, **id_kwargs):
        existing = yield self._exists(model, *id_args, **id_kwargs)
        msg = 'The following has *NOT* been found on the store: {} {}'.format(id_args, id_kwargs)
        self.assertTrue(existing, msg)

    @inlineCallbacks
    def assert_model_not_exists(self, model, *id_args, **id_kwargs):
        existing = yield self._exists(model, *id_args, **id_kwargs)
        msg = 'The following model has been found on the store: {} {}'.format(id_args, id_kwargs)
        self.assertFalse(existing, msg)

    @transact_ro
    def get_submissions_ids(self, store):
        return [s.id for s in store.find(models.InternalTip)]

    @transact_ro
    def get_rtips(self, store):
        ret = []
        for tip in store.find(models.ReceiverTip):
            x = rtip.serialize_rtip(store, tip, 'en')
            x['receiver_id'] = tip.receiver.id
            ret.append(x)

        return ret

    @transact_ro
    def get_rfiles(self, store, rtip_id):
        return [{'id': rfile.id} for rfile in store.find(models.ReceiverFile, models.ReceiverFile.receivertip_id == rtip_id)]

    @transact_ro
    def get_wbtips(self, store):
        ret = []
        for tip in store.find(models.WhistleblowerTip):
            x = wbtip.serialize_wbtip(store, tip, 'en')
            x['receivers_ids'] = [rcvr.id for rcvr in tip.internaltip.receivers]
            ret.append(x)

        return ret

    @transact_ro
    def get_internalfiles_by_wbtip(self, store, wbtip_id):
        wbtip = store.find(models.WhistleblowerTip, models.WhistleblowerTip.id == unicode(wbtip_id)).one()

        ifiles = store.find(models.InternalFile, models.InternalFile.internaltip_id == unicode(wbtip.internaltip_id))

        return [serialize_internalfile(ifil) for ifil in ifiles]


    @transact_ro
    def get_receiverfiles_by_wbtip(self, store, wbtip_id):
        wbtip = store.find(models.WhistleblowerTip, models.WhistleblowerTip.id == unicode(wbtip_id)).one()

        rfiles = store.find(models.ReceiverFile, models.ReceiverFile.internaltip_id == unicode(wbtip.internaltip_id))

        return [serialize_receiverfile(rfile) for rfile in rfiles]


class TestGLWithPopulatedDB(TestGL):
    @inlineCallbacks
    def setUp(self):
        yield TestGL.setUp(self)
        yield self.fill_data()

    def receiver_assertions(self, source_r, created_r):
        self.assertEqual(source_r['name'], created_r['name'], 'name')
        self.assertEqual(source_r['can_delete_submission'], created_r['can_delete_submission'], 'delete')

    def context_assertions(self, source_c, created_c):
        self.assertEqual(source_c['show_small_cards'], created_c['show_small_cards'])

    @inlineCallbacks
    def fill_data(self):
        # fill_data/create_admin
        self.dummyAdmin = yield create_admin(copy.deepcopy(self.dummyAdminUser), 'en')
        self.dummyAdminUser['id'] = self.dummyAdmin['id']

        # fill_data/create_custodian
        self.dummyCustodian = yield create_custodian(copy.deepcopy(self.dummyCustodianUser), 'en')
        self.dummyCustodianUser['id'] = self.dummyCustodian['id']

        # fill_data/create_receiver
        self.dummyReceiver_1 = yield create_receiver(copy.deepcopy(self.dummyReceiver_1), 'en')
        self.dummyReceiverUser_1['id'] = self.dummyReceiver_1['id']
        self.dummyReceiver_2 = yield create_receiver(copy.deepcopy(self.dummyReceiver_2), 'en')
        self.dummyReceiverUser_2['id'] = self.dummyReceiver_2['id']
        receivers_ids = [self.dummyReceiver_1['id'], self.dummyReceiver_2['id']]

        # fill_data/create_context
        self.dummyContext['receivers'] = receivers_ids
        self.dummyContext = yield create_context(copy.deepcopy(self.dummyContext), 'en')

        # fill_data: create field templates
        for idx, field in enumerate(self.dummyFieldTemplates):
            f = yield create_field(copy.deepcopy(field), 'en', 'import')
            self.dummyFieldTemplates[idx]['id'] = f['id']

        for idx, field in enumerate(self.dummyFields):
            change_field_type(field, 'instance')
            field['step_id'] = self.dummyContext['steps'][0]['id']
            f = yield create_field(copy.deepcopy(field), 'en', 'import')
            self.dummyFields[idx]['id'] = f['id']

            self.dummyContext['steps'][0]['children'].append(f)

        yield update_context(self.dummyContext['id'], copy.deepcopy(self.dummyContext), 'en')

    def perform_submission_start(self):
        self.dummyToken = token.Token(token_kind='submission')
        self.dummyToken.proof_of_work = False

    @inlineCallbacks
    def perform_submission_uploads(self):
        yield self.emulate_file_upload(self.dummyToken, 10)

    @inlineCallbacks
    def perform_submission_actions(self):
        self.dummySubmission['context_id'] = self.dummyContext['id']
        self.dummySubmission['receivers'] = self.dummyContext['receivers']
        self.dummySubmission['identity_provided'] = False
        self.dummySubmission['answers'] = yield self.fill_random_answers(self.dummyContext['id'])

        self.dummySubmission = yield create_submission(self.dummyToken.id,
                                                       self.dummySubmission, 
                                                       True, 'en')

    @inlineCallbacks
    def perform_post_submission_actions(self):
        commentCreation = {
            'content': 'comment!'
        }

        messageCreation = {
            'content': 'message!'
        }

        identityaccessrequestCreation = {
            'request_motivation': 'request motivation'
        }

        self.dummyRTips = yield self.get_rtips()

        for rtip_desc in self.dummyRTips:
            yield rtip.create_comment(rtip_desc['receiver_id'],
                                      rtip_desc['id'],
                                      commentCreation)

            yield rtip.create_message(rtip_desc['receiver_id'],
                                      rtip_desc['id'],
                                      messageCreation)

            yield self.emulate_file_append(rtip_desc['id'], 3)

            yield rtip.create_identityaccessrequest(rtip_desc['receiver_id'],
                                                    rtip_desc['id'],
                                                    identityaccessrequestCreation,
                                                    'en')

        self.dummyWBTips = yield self.get_wbtips()

        for wbtip_desc in self.dummyWBTips:
            yield wbtip.create_comment(wbtip_desc['id'],
                                       commentCreation)

            for receiver_id in wbtip_desc['receivers_ids']:
                yield wbtip.create_message(wbtip_desc['id'], receiver_id, messageCreation)

    @inlineCallbacks
    def perform_full_submission_actions(self):
        self.perform_submission_start()
        yield self.perform_submission_uploads()
        yield self.perform_submission_actions()
        yield self.perform_post_submission_actions()


class TestHandler(TestGLWithPopulatedDB):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    @inlineCallbacks
    def setUp(self):
        """
        override default handlers get_store with a mock store used for testing
        """
        # we bypass TestGLWith Populated DB to test against clean DB.
        yield TestGL.setUp(self)

        self.initialization()

    def initialization(self):
        self.responses = []

        def mock_write(cls, response=None):
            # !!!
            # Here we are making the assumption that every time write() get's
            # called it contains *all* of the response message.
            #RequestHandler.finish(cls, response)

            if response:
                self.responses.append(response)


        self._handler.write = mock_write
        # we make the assumption that we will always use call finish on write.
        self._handler.finish = mock_write

        # we need to reset settings.session to keep each test independent
        GLSettings.sessions.clear()

        # we need to reset GLApiCache to keep each test independent
        GLApiCache.invalidate()

    def request(self, jbody=None, user_id=None, role=None, headers=None, body='',
                remote_ip='0.0.0.0', method='MOCK', kwargs={}):

        """
        Function userful for performing mock requests.

        Args:

            jbody:
                The body of the request as a dict (it will be automatically
                converted to string)

            body:
                The body of the request as a string

            user_id:
                when simulating authentication the session should be bound
                to a certain user_id.

            role:
                when simulating authentication the session should be bound
                to a certain role.

            method:
                HTTP method, e.g. "GET" or "POST"

            uri:
                URL to fetch

            headers:
                (dict or :class:`cyclone.httputil.HTTPHeaders` instance) HTTP
                headers to pass on the request

            remote_ip:
                If a particular remote_ip should be set.

        """
        if jbody and not body:
            body = json.dumps(jbody)
        elif body and jbody:
            raise ValueError('jbody and body in conflict')

        application = Application([])

        tr = proto_helpers.StringTransport()
        connection = GLHTTPConnection()
        connection.factory = application
        connection.makeConnection(tr)

        request = httpserver.HTTPRequest(uri='mock',
                                         method=method,
                                         headers=headers,
                                         body=body,
                                         remote_ip=remote_ip,
                                         connection=connection)

        handler = self._handler(application, request, **kwargs)

        if role is not None:
            session = authentication.GLSession(user_id, role, 'enabled')
            handler.request.headers['X-Session'] = session.id

        return handler


class TestHandlerWithPopulatedDB(TestHandler):
    @inlineCallbacks
    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        yield TestGLWithPopulatedDB.setUp(self)
        self.initialization()


class MockDict():
    """
    This class just create all the shit we need for emulate a GLNode
    """

    def __init__(self):
        self.dummyUser = {
            'id': '',
            'username': u'maker@iz.cool.yeah',
            'password': VALID_PASSWORD1,
            'old_password': '',
            'salt': VALID_SALT1,
            'role': u'receiver',
            'state': u'enabled',
            'name': u'Generic User',
            'description': u'King MockDummy Generic User',
            'last_login': u'1970-01-01 00:00:00.000000',
            'timezone': 0,
            'language': u'en',
            'password_change_needed': False,
            'password_change_date': u'1970-01-01 00:00:00.000000',
            'pgp_key_info': u'',
            'pgp_key_fingerprint': u'',
            'pgp_key_status': u'disabled',
            'pgp_key_public': u'',
            'pgp_key_expiration': u'1970-01-01 00:00:00.000000',
            'pgp_key_remove': False
        }

        self.dummyReceiver = copy.deepcopy(self.dummyUser)

        self.dummyReceiver = sum_dicts(self.dummyReceiver, {
            'can_delete_submission': True,
            'can_postpone_expiration': True,
            'contexts': [],
            'tip_notification': True,
            'presentation_order': 0,
            'configuration': 'default'
        })

        self.dummyFieldTemplates = load_json_file(WHISTLEBLOWER_IDENTITY_FIELD_PATH)['children']
        for f in self.dummyFieldTemplates:
            f['fieldgroup_id'] = ''

        self.dummyFields = copy.deepcopy(self.dummyFieldTemplates)

        self.dummySteps = [
            {
                'id': '',
                'label': u'Step 1',
                'description': u'Step Description',
                'presentation_order': 0,
                'children': []
            },
            {
                'id': '',
                'label': u'Step 2',
                'description': u'Step Description',
                'hint': u'Step Hint',
                'presentation_order': 1,
                'children': []
            }
        ]

        self.dummyContext = {
            'id': '',
            'name': u'Already localized name',
            'description': u'Already localized desc',
            'recipients_clarification': u'',
            'presentation_order': 0,
            'receivers': [],
            'steps': [],
            'select_all_receivers': True,
            'tip_timetolive': 20,
            'maximum_selectable_receivers': 0,
            'show_small_cards': False,
            'show_context': True,
            'show_recipients_details': True,
            'allow_recipients_selection': False,
            'enable_comments': True,
            'enable_messages': True,
            'enable_two_way_comments': True,
            'enable_two_way_messages': True,
            'enable_attachments': True,
            'show_receivers_in_alphabetical_order': False,
            'questionnaire_layout': 'horizontal',
            'reset_questionnaire': True
        }

        self.dummySubmission = {
            'context_id': '',
            'answers': {},
            'receivers': [],
            'files': []
        }

        self.dummyNode = {
            'name': u"Please, set me: name/title",
            'description': u"Pleæs€, set m€: d€scription",
            'presentation': u'This is whæt æpp€ærs on top',
            'footer': u'check it out https://www.youtube.com/franksentus ;)',
            'security_awareness_title': u'',
            'security_awareness_text': u'',
            'whistleblowing_question': u'',
            'whistleblowing_button': u'',
            'hidden_service': u"http://1234567890123456.onion",
            'public_site': u"https://globaleaks.org",
            'email': u"email@dummy.net",
            'languages_supported': [],  # ignored
            'languages_enabled': ["it", "en"],
            'password': '',
            'old_password': '',
            'salt': 'OMG!, the Rains of Castamere ;( ;(',
            'salt_receipt': '<<the Lannisters send their regards>>',
            'maximum_filesize': 30,
            'maximum_namesize': 120,
            'maximum_textsize': 4096,
            'tor2web_admin': True,
            'tor2web_custodian': True,
            'tor2web_whistleblower': True,
            'tor2web_receiver': True,
            'tor2web_unauth': True,
            'can_postpone_expiration': False,
            'can_delete_submission': False,
            'can_grant_permissions': False,
            'ahmia': False,
            'allow_unencrypted': True,
            'allow_iframes_inclusion': False,
            'send_email_for_every_event': False,
            'custom_homepage': False,
            'disable_privacy_badge': False,
            'disable_security_awareness_badge': False,
            'disable_security_awareness_questions': False,
            'disable_key_code_hint': False,
            'disable_donation_panel': False,
            'default_timezone': 0,
            'default_language': u'en',
            'admin_timezone': 0,
            'admin_language': u'en',
            'simplified_login': False,
            'enable_captcha': False,
            'enable_proof_of_work': False,
            'enable_experimental_features': False,
            'enable_custom_privacy_badge': False,
            'custom_privacy_badge_tor': u'',
            'custom_privacy_badge_none': u'',
            'header_title_homepage': u'',
            'header_title_submissionpage': u'',
            'header_title_receiptpage': u'',
            'header_title_tippage': u'',
            'landing_page': u'homepage',
            'context_selector_label': u'',
            'show_contexts_in_alphabetical_order': False,
            'submission_minimum_delay': 123,
            'submission_maximum_ttl': 1111,
            'widget_comments_title': '',
            'widget_messages_title': '',
            'widget_files_title': '',
            'threshold_free_disk_megabytes_high': 200,
            'threshold_free_disk_megabytes_medium': 500,
            'threshold_free_disk_megabytes_low': 1000,
            'threshold_free_disk_percentage_high': 3,
            'threshold_free_disk_percentage_medium': 5,
            'threshold_free_disk_percentage_low': 10
        }
