# -*- coding: UTF-8

"""
Utilities and basic TestCases.
"""

from __future__ import with_statement

import copy
import json

import os
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


# Monkeypatching for unit testing  in order to
# prevent mail activities
from globaleaks.utils import mailutils

def sendmail_mock(**args):
    return defer.succeed(None)

mailutils.sendmail = sendmail_mock


from globaleaks import db, models, security, anomaly, event
from globaleaks.db.datainit import load_appdata, import_memory_variables
from globaleaks.handlers import files, rtip, wbtip, authentication
from globaleaks.handlers.base import GLHTTPConnection, BaseHandler
from globaleaks.handlers.admin.context import create_context, get_context, update_context, db_get_context_steps
from globaleaks.handlers.admin.receiver import create_receiver
from globaleaks.handlers.admin.field import create_field
from globaleaks.handlers.admin.user import create_admin, create_custodian
from globaleaks.handlers.wbtip import wb_serialize_tip
from globaleaks.handlers.submission import create_submission
from globaleaks.jobs import statistics_sched, mailflush_sched
from globaleaks.models import db_forge_obj, ReceiverTip, ReceiverFile, WhistleblowerTip, InternalTip
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings, transact, transact_ro
from globaleaks.security import GLSecureTemporaryFile
from globaleaks.third_party import rstr
from globaleaks.utils import token
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import sum_dicts, datetime_null, log

from . import TEST_DIR

## constants
VALID_PASSWORD1 = u'justapasswordwithaletterandanumberandbiggerthan8chars'
VALID_PASSWORD2 = u'justap455w0rdwithaletterandanumberandbiggerthan8chars'
VALID_SALT1 = security.get_salt(rstr.xeger(r'[A-Za-z0-9]{56}'))
VALID_SALT2 = security.get_salt(rstr.xeger(r'[A-Za-z0-9]{56}'))
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
authentication.reactor_override = task.Clock()
event.reactor_override = task.Clock()
token.reactor_override = task.Clock()
mailflush_sched.reactor_override = task.Clock()


class UTlog:
    @staticmethod
    def err(stuff):
        pass

    @staticmethod
    def debug(stuff):
        pass


log.err = UTlog.err
log.debug = UTlog.debug


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
    with open(os.path.join(FIXTURES_PATH, fixture)) as f:
        data = json.loads(f.read())
        for mock in data:
            if mock['class'] == 'Field':
                if mock['fields']['instance'] != 'reference':
                    del mock['fields']['template_id']

                if mock['fields']['step_id'] == '':
                    del mock['fields']['step_id']
                if mock['fields']['fieldgroup_id'] == '':
                    del mock['fields']['fieldgroup_id']

            mock_class = getattr(models, mock['class'])
            db_forge_obj(store, mock_class, mock['fields'])
            store.commit()


def get_file_upload(self):
    return self.request.body


BaseHandler.get_file_upload = get_file_upload


class TestGL(unittest.TestCase):
    encryption_scenario = 'MIXED'  # receivers with pgp and receivers without pgp

    create_node = True

    @inlineCallbacks
    def setUp(self):
        GLSettings.set_devel_mode()
        GLSettings.logging = None
        GLSettings.scheduler_threadpool = FakeThreadPool()
        GLSettings.sessions = {}
        GLSettings.failed_login_attempts = 0

        # Simulate two languages enabled that is somehow the most common configuration
        GLSettings.defaults.languages_enabled = ['en', 'it']

        if os.path.isdir('/dev/shm'):
            GLSettings.working_path = '/dev/shm/globaleaks'
            GLSettings.ramdisk_path = '/dev/shm/globaleaks/ramdisk'
        else:
            GLSettings.working_path = './working_path'
            GLSettings.ramdisk_path = './working_path/ramdisk'

        GLSettings.eval_paths()
        GLSettings.remove_directories()
        GLSettings.create_directories()

        self.setUp_dummy()

        yield db.create_tables(self.create_node)

        for fixture in getattr(self, 'fixtures', []):
            yield import_fixture(fixture)

        yield import_memory_variables()

        # override of imported memory variables
        GLSettings.memory_copy.allow_unencrypted = True

        anomaly.Alarm.reset()
        event.EventTrackQueue.reset()
        statistics_sched.StatisticsSchedule.reset()

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
            self.dummyReceiver_1['pgp_key_public'] = None
            self.dummyReceiver_2['pgp_key_public'] = VALID_PGP_KEY1
        elif self.encryption_scenario == 'ALL_ENCRYPTED':
            self.dummyReceiver_1['pgp_key_public'] = VALID_PGP_KEY1
            self.dummyReceiverUser_2['pgp_key_public'] = VALID_PGP_KEY2
        elif self.encryption_scenario == 'ONE_VALID_ONE_EXPIRED':
            self.dummyReceiver_1['pgp_key_public'] = VALID_PGP_KEY1
            self.dummyReceiver_2['pgp_key_public'] = EXPIRED_PGP_KEY
        elif self.encryption_scenario == 'ALL_PLAINTEXT':
            self.dummyReceiver_1['pgp_key_public'] = None
            self.dummyReceiver_2['pgp_key_public'] = None

        self.dummyNode = dummyStuff.dummyNode

        self.assertEqual(os.listdir(GLSettings.submission_path), [])
        self.assertEqual(os.listdir(GLSettings.tmp_upload_path), [])

    def localization_set(self, dict_l, dict_c, language):
        ret = dict(dict_l)

        for attr in getattr(dict_c, 'localized_strings'):
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
        new_r['ping_mail_address'] = unicode('%s@%s.xxx' % (descpattern, descpattern))

        return sum_dicts(new_r, new_u)

    def get_dummy_field(self):
        return {
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

        fill_localized_keys(field, models.Field.localized_strings, 'en')

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
        dummySubmissionDict = {}
        dummySubmissionDict['context_id'] = context_id
        dummySubmissionDict['receivers'] = (yield get_context(context_id, 'en'))['receivers']
        dummySubmissionDict['files'] = []
        dummySubmissionDict['human_captcha_answer'] = 0
        dummySubmissionDict['graph_captcha_answer'] = ''
        dummySubmissionDict['proof_of_work_answer'] = 0
        dummySubmissionDict['whistleblower_provided_identity'] = False
        dummySubmissionDict['answers'] = yield self.fill_random_answers(context_id)

        defer.returnValue(dummySubmissionDict)

    def get_dummy_file(self, filename=None, content_type=None, content=None):
        if filename is None:
            filename = ''.join(unichr(x) for x in range(0x400, 0x40A))

        if content_type is None:
            content_type = 'application/octet'

        if content is None:
            content = 'LA VEDI LA SUPERCAZZOLA ? PREMATURA ? unicode €'

        temporary_file = GLSecureTemporaryFile(GLSettings.tmp_upload_path)

        temporary_file.write(content)
        temporary_file.avoid_delete()

        dummy_file = {
            'body': temporary_file,
            'body_len': len(content),
            'body_filepath': temporary_file.filepath,
            'filename': filename,
            'content_type': content_type,
        }

        return dummy_file

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
    def emulate_file_append(self, tip_id, n):
        for i in range(0, n):
            dummyFile = self.get_dummy_file()

            dummyFile = yield threads.deferToThread(files.dump_file_fs, dummyFile)
            registered_file = yield files.register_file_db(
                dummyFile, tip_id,
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
        ids = []
        submissions = store.find(InternalTip)
        for s in submissions:
            ids.append(s.id)

        return ids

    @transact_ro
    def get_rtips(self, store):
        rtips_desc = []
        rtips = store.find(ReceiverTip)
        for r in rtips:
            itip = rtip.receiver_serialize_tip(store, r.internaltip, 'en')
            rtips_desc.append({'rtip_id': r.id, 'receiver_id': r.receiver_id, 'itip': itip})

        return rtips_desc

    @transact_ro
    def get_rfiles(self, store, rtip_id):
        rfiles_desc = []
        rfiles = store.find(ReceiverFile, ReceiverFile.receivertip_id == rtip_id)
        for rfile in rfiles:
            rfiles_desc.append({'rfile_id': rfile.id})

        return rfiles_desc

    @transact_ro
    def get_wbtips(self, store):
        wbtips_desc = []
        wbtips = store.find(WhistleblowerTip)
        for wbtip in wbtips:
            rcvrs_ids = []
            for rcvr in wbtip.internaltip.receivers:
                rcvrs_ids.append(rcvr.id)

            itip = wb_serialize_tip(store, wbtip.internaltip, 'en')
            wbtips_desc.append({'wbtip_id': wbtip.id, 'wbtip_receivers': rcvrs_ids, 'itip': itip})

        return wbtips_desc


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
        yield do_appdata_init()

        # fill_data/create_admin
        self.dummyAdmin = yield create_admin(copy.deepcopy(self.dummyAdminUser), 'en')
        self.dummyAdminUser['id'] = self.dummyAdmin['id']

        # fill_data/create_custodian
        self.dummyCustodian = yield create_custodian(copy.deepcopy(self.dummyCustodianUser), 'en')
        self.dummyCustodianUser['id'] = self.dummyCustodian['id']
        custodians_ids = [self.dummyCustodian['id']]

        # fill_data/create_receiver
        self.dummyReceiver_1 = yield create_receiver(copy.deepcopy(self.dummyReceiver_1), 'en')
        self.dummyReceiverUser_1['id'] = self.dummyReceiver_1['id']
        self.dummyReceiver_2 = yield create_receiver(copy.deepcopy(self.dummyReceiver_2), 'en')
        self.dummyReceiverUser_2['id'] = self.dummyReceiver_2['id']
        receivers_ids = [self.dummyReceiver_1['id'], self.dummyReceiver_2['id']]

        # fill_data/create_context
        self.dummyContext['custodians'] = custodians_ids
        self.dummyContext['receivers'] = receivers_ids
        self.dummyContext = yield create_context(copy.deepcopy(self.dummyContext), 'en')

        # fill_data: create field templates
        for idx, field in enumerate(self.dummyFieldTemplates):
            f = yield create_field(copy.deepcopy(field), 'en')
            self.dummyFieldTemplates[idx]['id'] = f['id']

        # fill_data: create fields and associate them to the context steps
        for idx, field in enumerate(self.dummyFields):
            field['instance'] = 'instance'
            if idx <= 2:
                # "Field 1", "Field 2" and "Generalities" are associated to the first step
                field['step_id'] = self.dummyContext['steps'][0]['id']
            else:
                # Name, Surname, Gender" are associated to field "Generalities"
                # "Field 1" and "Field 2" are associated to the first step
                field['fieldgroup_id'] = self.dummyFields[2]['id']

            f = yield create_field(copy.deepcopy(field), 'en')
            self.dummyFields[idx]['id'] = f['id']

        self.dummyContext['steps'][0]['children'] = [
            self.dummyFields[0],  # Field 1
            self.dummyFields[1],  # Field 2
            self.dummyFields[2]   # Generalities
        ]

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
        self.dummySubmission['whistleblower_provided_identity'] = False
        self.dummySubmission['answers'] = yield self.fill_random_answers(self.dummyContext['id'])

        self.dummySubmission = yield create_submission(self.dummyToken.id,
                                                       self.dummySubmission, 
                                                       True, 'en')

    @inlineCallbacks
    def perform_post_submission_actions(self):
        commentCreation = {
            'content': 'comment!',
        }

        messageCreation = {
            'content': 'message!',
        }

        identityaccessrequestCreation = {
            'request_motivation': 'request motivation'
        }

        self.dummyRTips = yield self.get_rtips()

        for rtip_desc in self.dummyRTips:
            yield rtip.create_comment_receiver(rtip_desc['receiver_id'],
                                               rtip_desc['rtip_id'],
                                               commentCreation)

            yield rtip.create_message_receiver(rtip_desc['receiver_id'],
                                               rtip_desc['rtip_id'],
                                               messageCreation)

            yield rtip.create_identityaccessrequest(rtip_desc['receiver_id'],
                                                    rtip_desc['rtip_id'],
                                                    identityaccessrequestCreation,
                                                    'en')

        self.dummyWBTips = yield self.get_wbtips()

        for wbtip_desc in self.dummyWBTips:
            yield wbtip.create_comment_wb(wbtip_desc['wbtip_id'],
                                          commentCreation)

            for receiver_id in wbtip_desc['wbtip_receivers']:
                yield wbtip.create_message_wb(wbtip_desc['wbtip_id'], receiver_id, messageCreation)

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
        override default handlers' get_store with a mock store used for testing/
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
        GLSettings.sessions = dict()

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
            'mail_address': self.dummyUser['username'],
            'ping_mail_address': 'giovanni.pellerano@evilaliv3.org',
            'can_delete_submission': True,
            'can_postpone_expiration': True,
            'contexts': [],
            'tip_notification': True,
            'ping_notification': True,
            'tip_expiration_threshold': 72,
            'presentation_order': 0,
            'configuration': 'default',
            'pgp_key_info': u'',
            'pgp_key_fingerprint': u'',
            'pgp_key_status': u'disabled',
            'pgp_key_public': u'',
            'pgp_key_expiration': u'1970-01-01 00:00:00.000000',
            'pgp_key_remove': False
        })

        self.dummyFieldTemplates = [
            {
                'id': u'd4f06ad1-eb7a-4b0d-984f-09373520cce7',
                'key': '',
                'instance': 'template',
                'editable': True,
                'template_id': '',
                'step_id': '',
                'fieldgroup_id': '',
                'label': u'Field 222',
                'type': u'inputbox',
                'preview': False,
                'description': u'field description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': True,  # <- first field is special,
                'children': [],    # it's marked as required!!!
                'attrs': {},
                'options': [],
                'y': 2,
                'x': 0,
                'width': 0
            },
            {
                'id': u'c4572574-6e6b-4d86-9a2a-ba2e9221467d',
                'key': '',
                'instance': 'template',
                'editable': True,
                'template_id': '',
                'step_id': '',
                'fieldgroup_id': '',
                'label': u'Field 2',
                'type': u'inputbox',
                'preview': False,
                'description': 'description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': False,
                'children': [],
                'attrs': {},
                'options': [],
                'y': 3,
                'x': 0,
                'width': 0
            },
            {
                'id': u'6a6e9282-15e8-47cd-9cc6-35fd40a4a58f',
                'key': '',
                'instance': 'template',
                'editable': True,
                'step_id': '',
                'template_id': '',
                'fieldgroup_id': '',
                'label': u'Generalities',
                'type': u'fieldgroup',
                'preview': False,
                'description': u'field description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': False,
                'children': [],
                'attrs': {},
                'options': [],
                'y': 4,
                'x': 0,
                'width': 0
            },
            {
                'id': u'7459abe3-52c9-4a7a-8d48-cabe3ffd2abd',
                'key': '',
                'instance': 'template',
                'editable': True,
                'template_id': '',
                'step_id': '',
                'fieldgroup_id': '',
                'label': u'Name',
                'type': u'inputbox',
                'preview': False,
                'description': u'field description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': False,
                'children': [],
                'attrs': {},
                'options': [],
                'y': 0,
                'x': 0,
                'width': 0
            },
            {
                'id': u'de1f0cf8-63a7-4ed8-bc5d-7cf0e5a2aec2',
                'key': '',
                'instance': 'template',
                'editable': True,
                'template_id': '',
                'step_id': '',
                'fieldgroup_id': '',
                'label': u'Surname',
                'type': u'inputbox',
                'preview': False,
                'description': u'field description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': False,
                'children': [],
                'attrs': {},
                'options': [],
                'y': 0,
                'x': 0,
                'width': 0
            },
            {
                'id': u'7e1f0cf8-63a7-4ed8-bc5d-7cf0e5a2aec2',
                'key': '',
                'instance': 'template',
                'editable': True,
                'template_id': '',
                'step_id': '',
                'fieldgroup_id': '',
                'label': u'Gender',
                'type': u'selectbox',
                'preview': False,
                'description': u'field description',
                'hint': u'field hint',
                'multi_entry': False,
                'multi_entry_hint': '',
                'stats_enabled': False,
                'required': False,
                'children': [],
                'attrs': {},
                'options': [
                    {
                        'id': '2ebf6df8-289a-4f17-aa59-329fe11d232e',
                        'label': 'Male',
                        'value': '',
                        'presentation_order': 0,
                        'score_points': 0,
                        'activated_fields': [],
                        'activated_steps': []
                    },
                    {
                        'id': '9c7f343b-ed46-4c9e-9121-a54b6e310123',
                        'label': 'Female',
                        'value': '',
                        'presentation_order': 0,
                        'score_points': 0,
                        'activated_fields': [],
                        'activated_steps': []
                    }
                ],
                'y': 0,
                'x': 0,
                'width': 0
            }]

        self.dummyFields = copy.deepcopy(self.dummyFieldTemplates)

        self.dummySteps = [
            {
                'label': u'Step 1',
                'description': u'Step Description',
                'hint': u'Step Hint',
                'presentation_order': 0,
                'children': []
            },
            {
                'label': u'Step 2',
                'description': u'Step Description',
                'hint': u'Step Hint',
                'presentation_order': 1,
                'children': []
            }
        ]

        self.dummyContext = {
            # localized stuff
            'name': u'Already localized name',
            'description': u'Already localized desc',
            'presentation_order': 0,
            'custodians': [],
            'receivers': [],
            'steps': [],
            'select_all_receivers': True,
            # tip_timetolive is expressed in days
            'tip_timetolive': 20,
            'maximum_selectable_receivers': 0,
            'show_small_cards': False,
            'show_context': True,
            'show_receivers': False,
            'enable_comments': True,
            'enable_messages': True,
            'enable_two_way_communication': True,
            'enable_attachments': True,
            'show_receivers_in_alphabetical_order': False,
            'steps_arrangement': 'horizontal',
            'reset_steps': False
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
            'maximum_filesize': GLSettings.defaults.maximum_filesize,
            'maximum_namesize': GLSettings.defaults.maximum_namesize,
            'maximum_textsize': GLSettings.defaults.maximum_textsize,
            'tor2web_admin': True,
            'tor2web_custodian': True,
            'tor2web_whistleblower': True,
            'tor2web_receiver': True,
            'tor2web_unauth': True,
            'can_postpone_expiration': False,
            'can_delete_submission': False,
            'ahmia': False,
            'allow_unencrypted': True,
            'allow_iframes_inclusion': False,
            'send_email_for_every_event': False,
            'configured': False,
            'wizard_done': False,
            'custom_homepage': False,
            'disable_privacy_badge': False,
            'disable_security_awareness_badge': False,
            'disable_security_awareness_questions': False,
            'disable_key_code_hint': False,
            'default_timezone': 0,
            'default_language': u'en',
            'admin_timezone': 0,
            'admin_language': u'en',
            'simplified_login': False,
            'enable_captcha': False,
            'enable_proof_of_work': False,
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
            'widget_files_title': ''
        }


@transact
def do_appdata_init(store):
    try:
        appdata = store.find(models.ApplicationData).one()

        if not appdata:
            raise Exception

    except Exception:
        appdata = models.ApplicationData()
        source = load_appdata()
        appdata.version = source['version']
        appdata.fields = source['fields']
        store.add(appdata)
