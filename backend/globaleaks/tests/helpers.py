# -*- coding: utf-8
"""
Utilities and basic TestCases.
"""
import sys

try:  # Python 2
    reload(sys)  # pylint: disable=undefined-variable
    sys.setdefaultencoding('utf8')  # pylint: disable=no-member
except NameError:
    pass  # Python 3

import base64
import copy
import json
import os
import shutil
import signal
import six

from datetime import timedelta

# pylint: disable=no-name-in-module
from distutils import dir_util

from six import text_type, binary_type
from six.moves.urllib.parse import urlsplit  # pylint: disable=import-error

from twisted.internet import defer, task
from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.protocol import ProcessProtocol
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest

from . import TEST_DIR


from globaleaks import db, models, orm, event, jobs, __version__, DATABASE_VERSION
from globaleaks.db.appdata import load_appdata
from globaleaks.orm import transact, tw
from globaleaks.handlers import rtip, wbtip
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.context import create_context, get_context
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.handlers.admin.questionnaire import get_questionnaire, db_get_questionnaire
from globaleaks.handlers.admin.step import create_step
from globaleaks.handlers.admin.tenant import create as create_tenant
from globaleaks.handlers.admin.user import create_user
from globaleaks.handlers.wizard import db_wizard
from globaleaks.handlers.submission import create_submission
from globaleaks.models.config import db_set_config_variable
from globaleaks.rest import decorators
from globaleaks.sessions import Sessions
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils import tempdict, token, utility
from globaleaks.utils.crypto import GCE
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.securetempfile import SecureTemporaryFile
from globaleaks.utils.utility import datetime_null, datetime_now, datetime_to_ISO8601, \
    sum_dicts
from globaleaks.utils.log import log

from globaleaks.workers import process
from globaleaks.workers.supervisor import ProcessSupervisor

GCE.ALGORITM_CONFIGURATION['KDF']['ARGON2']['OPSLIMIT'] = GCE.ALGORITM_CONFIGURATION['HASH']['ARGON2']['OPSLIMIT'] = 1
GCE.ALGORITM_CONFIGURATION['HASH']['SCRYPT']['N'] = 1<<1

################################################################################
# BEGIN MOCKS NECESSARY FOR DETERMINISTIC ENCRYPTION
VALID_PASSWORD1 = u'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#'
VALID_PASSWORD2 = VALID_PASSWORD1
VALID_SALT1 = GCE.generate_salt()
VALID_SALT2 = GCE.generate_salt()
VALID_HASH1 = GCE.hash_password(VALID_PASSWORD1, VALID_SALT1)
VALID_HASH2 = GCE.hash_password(VALID_PASSWORD2, VALID_SALT2)
VALID_BASE64_IMG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQYV2NgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
INVALID_PASSWORD = u'antani'

KEY = GCE.generate_key()
USER_KEY = GCE.derive_key(VALID_PASSWORD1, VALID_SALT1)
USER_PRV_KEY, USER_PUB_KEY = GCE.generate_keypair()
USER_PRV_KEY_ENC = GCE.symmetric_encrypt(USER_KEY, USER_PRV_KEY)
GCE_orig_generate_key = GCE.generate_key
GCE_orig_generate_keypair = GCE.generate_keypair


@staticmethod
def GCE_mock_generate_key():
    return KEY


@staticmethod
def GCE_mock_generate_keypair():
    return USER_PRV_KEY, USER_PUB_KEY


setattr(GCE, 'generate_key', GCE_mock_generate_key)
setattr(GCE, 'generate_keypair', GCE_mock_generate_keypair)
# END MOCKS NECESSARY FOR DETERMINISTIC ENCRYPTION
################################################################################

PGPKEYS = {}

DATA_DIR = os.path.join(TEST_DIR, 'data')
kp = os.path.join(DATA_DIR, 'gpg')
for filename in os.listdir(kp):
    with open(os.path.join(kp, filename)) as pgp_file:
        PGPKEYS[filename] = text_type(pgp_file.read())


def deferred_sleep_mock(seconds):
    return


utility.deferred_sleep = deferred_sleep_mock


class UTlog:
    @staticmethod
    def mlog(flag):
        def log(msg, *args, **kwargs):
            msg = (msg % args) if len(args) else msg

            with open('./test.log', 'a') as f:
                f.write('[{}] {}\n'.format(flag, msg))

        return log


log.err = UTlog.mlog('E')
log.debug = UTlog.mlog('D')
log.info = UTlog.mlog('I')


token.Token.min_ttl = 0


class FakeThreadPool(object):
    """
    A fake L{twisted.python.threadpool.ThreadPool}, running functions inside
    the main thread instead for easing tests.
    """

    def callInThreadWithCallback(self, onResult, func, *args, **kw):
        success = True
        try:
            result = func(*args, **kw)
        except:
            result = Failure()
            success = False

        onResult(success, result)


def init_state():
    Settings.testing = True
    Settings.set_devel_mode()
    Settings.logging = None
    Settings.failed_login_attempts = 0
    Settings.working_path = os.path.abspath('./working_path')

    Settings.eval_paths()

    if os.path.exists(Settings.working_path):
        dir_util.remove_tree(Settings.working_path, 0)

    orm.set_thread_pool(FakeThreadPool())

    State.settings.enable_api_cache = False
    State.tenant_cache[1] = ObjectDict()
    State.tenant_cache[1].hostname = 'www.globaleaks.org'
    State.tenant_cache[1].encryption = True

    State.init_environment()

    Sessions.clear()


@transact
def mock_users_keys(session):
    for user in session.query(models.User):
        user.password = VALID_HASH1
        user.salt = VALID_SALT1
        user.crypto_prv_key = USER_PRV_KEY_ENC
        user.crypto_pub_key = USER_PUB_KEY


@transact
def associate_users_of_first_tenant_to_second_tenant(session):
    users_of_tenant_1 = session.query(models.User).filter(models.User.tid == 1)
    for user in users_of_tenant_1:
        user_tenant = models.UserTenant()
        user_tenant.user_id = user.id
        user_tenant.tenant_id = 2
        session.add(user_tenant)


def get_dummy_step():
    return {
        'id': '',
        'label': u'Step 1',
        'description': u'Step Description',
        'presentation_order': 0,
        'triggered_by_score': 0,
        'questionnaire_id': u'',
        'children': []
    }


def get_dummy_field():
    return {
        'id': '',
        'instance': 'template',
        'editable': True,
        'template_id': '',
        'template_override_id': '',
        'step_id': '',
        'fieldgroup_id': '',
        'label': u'antani',
        'type': u'checkbox',
        'preview': False,
        'description': u'field description',
        'hint': u'field hint',
        'multi_entry': False,
        'multi_entry_hint': '',
        'encrypt': False,
        'required': False,
        'attrs': {},
        'options': get_dummy_fieldoption_list(),
        'children': [],
        'y': 1,
        'x': 1,
        'width': 0,
        'triggered_by_score': 0
    }


def get_dummy_fieldoption_list():
    return [
        {
          'id': u'beefcafe-beef-cafe-beef-cafebeefcafe',
          'label': u'Cafe del mare',
          'presentation_order': 0,
          'score_points': 100,
          'score_type': 0,
          'trigger_field': '',
          'trigger_field_inverted': False,
          'trigger_step': '',
          'trigger_step_inverted': False,
          'trigger_receiver': []
        },
        {
          'id': u'feefbead-feef-bead-feef-feeffeefbead',
          'label': u'skrilx is here',
          'presentation_order': 0,
          'score_points': 97,
          'score_type': 0,
          'trigger_field': '',
          'trigger_field_inverted': False,
          'trigger_step': '',
          'trigger_step_inverted': False,
          'trigger_receiver': []
        }
    ]


files_count = 0


def get_dummy_file(filename=None, content=None):
    global files_count
    files_count += 1

    if filename is None:
        filename = ''.join(six.unichr(x) for x in range(0x400, 0x40A)).join('-%d' % files_count)

    content_type = u'application/octet'

    if content is None:
        content = base64.b64decode(VALID_BASE64_IMG)

    temporary_file = SecureTemporaryFile(Settings.tmp_path)

    with temporary_file.open('w') as f:
        f.write(content)
        f.finalize_write()

    State.TempUploadFiles[os.path.basename(temporary_file.filepath)] = temporary_file

    return {
        'date': datetime_now(),
        'name': filename,
        'description': 'description',
        'body': temporary_file,
        'size': len(content),
        'filename': os.path.basename(temporary_file.filepath),
        'type': content_type,
        'submission': False
    }


def get_file_upload(self):
    return get_dummy_file()


BaseHandler.get_file_upload = get_file_upload


def forge_request(uri=b'https://www.globaleaks.org/',
                  headers=None, body='', client_addr=None, method=b'GET'):
    """
    Creates a twisted.web.Request compliant request that is from an external
    IP address.
    """
    if headers is None:
        headers = {}

    _, host, path, query, frag = urlsplit(uri)

    x = host.split(b':')
    if len(x) > 1:
        port = int(x[1])
    else:
        port = 80

    request = DummyRequest([b''])
    request.tid = 1
    request.method = method
    request.uri = uri
    request.path = path
    request._serverName = host

    request.code = 200
    request.client_ip = b'127.0.0.1'
    request.client_proto = b'https'
    request.client_using_tor = False

    def getResponseBody():
        # Ugh, hack. Twisted returns this all as bytes, and we want it as str
        if isinstance(request.written[0], binary_type):
            return b''.join(request.written)
        else:
            return ''.join(request.written)

    request.getResponseBody = getResponseBody

    if client_addr is None:
        request.client = IPv4Address('TCP', b'1.2.3.4', 12345)
    else:
        request.client = client_addr

    def getHost():
        return IPv4Address('TCP', b'127.0.0.1', port)

    request.getHost = getHost

    def notifyFinish():
        return Deferred()

    request.notifyFinish = notifyFinish

    request.requestHeaders.setRawHeaders('host', [b'127.0.0.1'])
    request.requestHeaders.setRawHeaders('user-agent', [b'NSA Agent'])

    for k, v in headers.items():
        request.requestHeaders.setRawHeaders(k, [v])

    request.headers = request.getAllHeaders()

    class fakeBody(object):
        def read(self):
            if isinstance(body, dict):
                ret = json.dumps(body)
            else:
                ret = body

            if isinstance(ret, text_type):
                ret = ret.encode('utf-8')

            return ret

        def close(self):
            pass

    request.content = fakeBody()

    return request


class TestGL(unittest.TestCase):
    initialize_test_database_using_archived_db = True
    encryption_scenario = 'ENCRYPTED'

    @inlineCallbacks
    def setUp(self):
        self.test_reactor = task.Clock()

        jobs.job.reactor = self.test_reactor
        tempdict.reactor = self.test_reactor
        token.TokenList.reactor = self.test_reactor
        Sessions.reactor = self.test_reactor

        self.state = State

        init_state()

        self.setUp_dummy()

        if self.initialize_test_database_using_archived_db:
            shutil.copy(
                os.path.join(TEST_DIR, 'db', 'empty', 'glbackend-%d.db' % DATABASE_VERSION),
                os.path.join(Settings.db_file_path)
            )
        else:
            yield db.create_db()
            yield db.init_db()

        allow_unencrypted = self.encryption_scenario in ['PLAINTEXT', 'MIXED']

        yield tw(db_set_config_variable, 1, u'allow_unencrypted', allow_unencrypted)

        yield self.set_hostnames(1)

        yield db.refresh_memory_variables()

        sup = ProcessSupervisor([], '127.0.0.1', 8082)
        self.state.process_supervisor = sup

        self.state.reset_hourly()

        Settings.submission_minimum_delay = 0

        self.internationalized_text = load_appdata()['node']['whistleblowing_button']

    def call_spigot(self):
        """
        Required for clearing scheduled callbacks in the testReactor that have yet to run.
        If a unittest has scheduled something, we execute it before moving on.
        """
        deferred_fns = self.test_reactor.getDelayedCalls()
        i = 0
        while len(deferred_fns) != 0:
            yield deferred_fns[0].getTime()
            if i >= 30:
                raise Exception("stuck in callback loop")
            i += 1
            deferred_fns = self.test_reactor.getDelayedCalls()
        raise StopIteration

    def tearDown(self):
        self.test_reactor.pump(self.call_spigot())

    @transact
    def set_hostnames(self, session, i):
        hosts = [('www.globaleaks.org', 'aaaaaaaaaaaaaaaa.onion'),
                 ('www.domain-a.com', 'bbbbbbbbbbbbbbbb.onion'),
                 ('www.domain-b.com', 'cccccccccccccccc.onion')]

        hostname, onionservice = hosts[i - 1]
        db_set_config_variable(session, i, 'hostname', hostname)
        db_set_config_variable(session, i, 'onionservice', onionservice)

    def setUp_dummy(self):
        dummyStuff = MockDict()

        self.dummyWizard = {
            'node_language': u'en',
            'node_name': 'test',
            'admin_name': 'Giovanni Pellerano',
            'admin_password': 'P4ssword',
            'admin_mail_address': 'evilaliv3@globaleaks.org',
            'receiver_name': 'Fabio Pietrosanti',
            'receiver_password': 'P4ssword',
            'receiver_mail_address': 'naif@globaleaks.org',
            'profile': 'default',
            'enable_developers_exception_notification': True
        }

        self.dummySignup = {
            'name': 'Raffaele',
            'surname': 'Cantone',
            'role': '',
            'email': 'raffaele.cantone@anticorruzione.it',
            'phone': '',
            'subdomain': 'ringobongo',
            'use_case': 'anticorruption',
            'use_case_other': '',
            'organization_name': '',
            'organization_type': '',
            'organization_location1': '',
            'organization_location2': '',
            'organization_location3': '',
            'organization_location4': '',
            'organization_site': '',
            'organization_number_employees': '',
            'organization_number_users': '',
            'hear_channel': '',
            'tos1': True,
            'tos2': True
        }

        self.dummyContext = dummyStuff.dummyContext
        self.dummySubmission = dummyStuff.dummySubmission
        self.dummyAdminUser = self.get_dummy_user('admin', 'admin')
        self.dummyCustodianUser = self.get_dummy_user('custodian', 'custodian1')
        self.dummyReceiverUser_1 = self.get_dummy_user('receiver', 'receiver1')
        self.dummyReceiverUser_2 = self.get_dummy_user('receiver', 'receiver2')
        self.dummyReceiver_1 = self.get_dummy_receiver('receiver1')  # the one without PGP
        self.dummyReceiver_2 = self.get_dummy_receiver('receiver2')  # the one with PGP

        if self.encryption_scenario == 'ENCRYPTED':
            self.dummyReceiver_1['pgp_key_public'] = PGPKEYS['VALID_PGP_KEY1_PUB']
            self.dummyReceiver_2['pgp_key_public'] = PGPKEYS['VALID_PGP_KEY2_PUB']
        elif self.encryption_scenario == 'ENCRYPTED_WITH_ONE_KEY_MISSING':
            self.dummyReceiver_1['pgp_key_public'] = PGPKEYS['VALID_PGP_KEY1_PUB']
            self.dummyReceiver_2['pgp_key_public'] = ''
        elif self.encryption_scenario == 'ENCRYPTED_WITH_ONE_KEY_EXPIRED':
            self.dummyReceiver_1['pgp_key_public'] = PGPKEYS['VALID_PGP_KEY1_PUB']
            self.dummyReceiver_2['pgp_key_public'] = PGPKEYS['EXPIRED_PGP_KEY_PUB']
        if self.encryption_scenario == 'MIXED':
            self.dummyReceiver_1['pgp_key_public'] = ''
            self.dummyReceiver_2['pgp_key_public'] = PGPKEYS['VALID_PGP_KEY1_PUB']
        elif self.encryption_scenario == 'PLAINTEXT':
            self.dummyReceiver_1['pgp_key_public'] = ''
            self.dummyReceiver_2['pgp_key_public'] = ''

        self.dummyNode = dummyStuff.dummyNode

        self.assertEqual(os.listdir(Settings.attachments_path), [])
        self.assertEqual(os.listdir(Settings.tmp_path), [])

    def get_dummy_user(self, role, username):
        new_u = dict(MockDict().dummyUser)
        new_u['role'] = role
        new_u['username'] = username
        new_u['name'] = new_u['mail_address'] = \
            text_type("%s@%s.xxx" % (username, username))
        new_u['description'] = u''
        new_u['password'] = VALID_PASSWORD1
        new_u['state'] = u'enabled'
        new_u['salt'] = VALID_SALT1

        return new_u

    def get_dummy_receiver(self, username):
        new_u = self.get_dummy_user('receiver', username)
        new_r = dict(MockDict().dummyReceiver)

        return sum_dicts(new_r, new_u)

    def fill_random_field_recursively(self, answers, field):
        field_type = field['type']

        if field_type == 'checkbox':
            value = {}
            for option in field['options']:
                value[option['id']] = 'True'
        elif field_type == 'selectbox':
            value = {'value': field['options'][0]['id']}
        elif field_type == 'date':
            value = {'value': datetime_to_ISO8601(datetime_now())}
        elif field_type == 'tos':
            value = {'value': 'True'}
        elif field_type == 'fieldgroup':
            value = {}
            for child in field['children']:
                self.fill_random_field_recursively(value, child)
        else:
            value = {'value': text_type(''.join(six.unichr(x) for x in range(0x400, 0x4FF)))}

        answers[field['id']] = [value]

    @transact
    def fill_random_answers(self, session, questionnaire_id, value=None):
        """
        return randomly populated questionnaire
        """
        answers = {}

        questionnaire = db_get_questionnaire(session, 1, questionnaire_id, 'en')

        for step in questionnaire['steps']:
            for field in step['children']:
                self.fill_random_field_recursively(answers, field)

        return answers

    def getToken(self, kind='submission'):
        return self.state.tokens.new(1, kind)

    def getSolvedToken(self, kind='submission'):
        t = self.getToken(kind)
        t.solved = True
        return t

    @inlineCallbacks
    def get_dummy_submission(self, context_id):
        """
        this may works until the content of the fields do not start to be validated. like
        numbers shall contain only number, and not URL.
        This validation would not be implemented in validate_jmessage but in structures.Fields

        need to be enhanced generating appropriate data based on the fields.type
        """
        context = yield get_context(1, context_id, 'en')
        answers = yield self.fill_random_answers(context['questionnaire_id'])

        defer.returnValue({
            'context_id': context_id,
            'receivers': context['receivers'],
            'files': [],
            'answer': 0,
            'identity_provided': False,
            'total_score': 0,
            'answers': answers
        })

    def get_dummy_file(self, filename='', content=None):
        return get_dummy_file(filename, content)

    def get_dummy_shorturl(self, x=''):
        return {
          'shorturl': 'shorturl' + str(x),
          'longurl': '/longurl' + str(x)
        }

    def emulate_file_upload(self, token, n):
        """
        This emulates the file upload of an incomplete submission
        """
        for _ in range(n):
            token.associate_file(self.get_dummy_file())

    def pollute_events(self, number_of_times=10):
        for _ in range(number_of_times):
            for event_obj in event.events_monitored:
                for x in range(2):
                    e = event.Event(event_obj, timedelta(seconds=1.0 * x))
                    self.state.tenant_state[1].RecentEventQ.append(e)
                    self.state.tenant_state[1].EventQ.append(e)

    @transact
    def get_rtips(self, session):
        ret = []
        for r, i in session.query(models.ReceiverTip, models.InternalTip) \
                         .filter(models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                 models.InternalTip.tid == 1):
            ret.append(rtip.serialize_rtip(session, r, i, 'en'))

        return ret

    @transact
    def get_rfiles(self, session, rtip_id):
        return [{'id': rfile.id} for rfile in session.query(models.ReceiverFile).filter(models.ReceiverFile.receivertip_id == rtip_id,
                                                                                        models.ReceiverTip.id == rtip_id,
                                                                                        models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                                                                        models.InternalTip.tid == 1)]

    @transact
    def get_wbtips(self, session):
        ret = []
        for w, i in session.query(models.WhistleblowerTip, models.InternalTip) \
                           .filter(models.WhistleblowerTip.id == models.InternalTip.id,
                                   models.InternalTip.tid == 1):
            x = wbtip.serialize_wbtip(session, w, i, 'en')
            x['receivers_ids'] = list(zip(*session.query(models.ReceiverTip.receiver_id)
                                           .filter(models.ReceiverTip.internaltip_id == i.id,
                                                   models.InternalTip.id == i.id,
                                                   models.InternalTip.tid == 1)))[0]
            ret.append(x)

        return ret

    @transact
    def get_wbfiles(self, session, wbtip_id):
        return [{'id': wbfile.id} for wbfile in session.query(models.WhistleblowerFile)
                                                     .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                                             models.ReceiverTip.internaltip_id == wbtip_id,
                                                             models.InternalTip.id == wbtip_id,
                                                             models.InternalTip.tid == 1)]

    @transact
    def get_internalfiles_by_receipt(self, session, receipt):
        hashed_receipt = GCE.hash_password(receipt, State.tenant_cache[1].receipt_salt)

        ifiles = session.query(models.InternalFile) \
                        .filter(models.InternalFile.internaltip_id == models.WhistleblowerTip.id,
                                models.WhistleblowerTip.receipt_hash == hashed_receipt)

        return [models.serializers.serialize_ifile(session, ifile) for ifile in ifiles]

    @transact
    def get_receiverfiles_by_receipt(self, session, receipt):
        hashed_receipt = GCE.hash_password(receipt, State.tenant_cache[1].receipt_salt)

        rfiles = session.query(models.ReceiverFile) \
                        .filter(models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                                models.ReceiverTip.internaltip_id == models.WhistleblowerTip.id,
                                models.WhistleblowerTip.receipt_hash == hashed_receipt)

        return [models.serializers.serialize_rfile(session, 1, rfile) for rfile in rfiles]

    def db_test_model_count(self, session, model, n):
        self.assertEqual(session.query(model).count(), n)

    @transact
    def test_model_count(self, session, model, n):
        self.db_test_model_count(session, model, n)

    @transact
    def get_model_count(self, session, model):
        return session.query(model).count()


class TestGLWithPopulatedDB(TestGL):
    complex_field_population = False
    population_of_recipients = 2
    population_of_submissions = 2
    population_of_attachments = 2
    population_of_tenants = 3

    @inlineCallbacks
    def setUp(self):
        yield TestGL.setUp(self)
        yield self.fill_data()
        yield db.refresh_memory_variables()

    @inlineCallbacks
    def fill_data(self):
        # fill_data/create_admin
        self.dummyAdminUser = yield create_user(1, copy.deepcopy(self.dummyAdminUser), 'en')

        # fill_data/create_custodian
        self.dummyCustodianUser = yield create_user(1, copy.deepcopy(self.dummyCustodianUser), 'en')

        # fill_data/create_receiver
        self.dummyReceiver_1 = yield create_user(1, copy.deepcopy(self.dummyReceiver_1), 'en')
        self.dummyReceiverUser_1['id'] = self.dummyReceiver_1['id']
        self.dummyReceiver_2 = yield create_user(1, copy.deepcopy(self.dummyReceiver_2), 'en')
        self.dummyReceiverUser_2['id'] = self.dummyReceiver_2['id']
        receivers_ids = [self.dummyReceiver_1['id'], self.dummyReceiver_2['id']]

        yield mock_users_keys()

        # fill_data/create_context
        self.dummyContext['receivers'] = receivers_ids
        self.dummyContext = yield create_context(1, copy.deepcopy(self.dummyContext), 'en')

        self.dummyQuestionnaire = yield get_questionnaire(1, self.dummyContext['questionnaire_id'], 'en')

        self.dummyQuestionnaire['steps'].append(get_dummy_step())
        self.dummyQuestionnaire['steps'][1]['questionnaire_id'] = self.dummyContext['questionnaire_id']
        self.dummyQuestionnaire['steps'][1]['label'] = 'Whistleblower identity'
        self.dummyQuestionnaire['steps'][1]['presentation_order'] = 1
        self.dummyQuestionnaire['steps'][1] = yield create_step(1, self.dummyQuestionnaire['steps'][1], 'en')

        if self.complex_field_population:
            yield self.add_whistleblower_identity_field_to_step(self.dummyQuestionnaire['steps'][1]['id'])

        for i in range(1, self.population_of_tenants):
            name = 'tenant-' + str(i+1)
            t = yield create_tenant({'mode': 'default', 'label': name, 'active': True, 'subdomain': name})
            yield tw(db_wizard, t['id'], self.dummyWizard, True, u'en')
            yield self.set_hostnames(i+1)

        yield associate_users_of_first_tenant_to_second_tenant()

    @transact
    def add_whistleblower_identity_field_to_step(self, session, step_id):
        wbf = session.query(models.Field).filter(models.Field.id == u'whistleblower_identity', models.Field.tid == 1).one()

        reference_field = get_dummy_field()
        reference_field['instance'] = 'reference'
        reference_field['template_id'] = wbf.id
        reference_field['step_id'] = step_id
        db_create_field(session, 1, reference_field, 'en')

    def perform_submission_start(self):
        return self.getSolvedToken()

    def perform_submission_uploads(self, token):
        for _ in range(self.population_of_attachments):
            token.associate_file(self.get_dummy_file())

    @inlineCallbacks
    def perform_submission_actions(self, token):
        self.dummySubmission['context_id'] = self.dummyContext['id']
        self.dummySubmission['receivers'] = self.dummyContext['receivers']
        self.dummySubmission['identity_provided'] = False
        self.dummySubmission['answers'] = yield self.fill_random_answers(self.dummyContext['questionnaire_id'])
        self.dummySubmission['total_score'] = 0

        self.dummySubmission = yield create_submission(1,
                                                       self.dummySubmission,
                                                       token,
                                                       True)

    @inlineCallbacks
    def perform_post_submission_actions(self):
        self.dummyRTips = yield self.get_rtips()

        for rtip_desc in self.dummyRTips:
            yield rtip.create_comment(1,
                                      rtip_desc['receiver_id'],
                                      USER_PRV_KEY,
                                      rtip_desc['id'],
                                      'comment')

            yield rtip.create_message(1,
                                      rtip_desc['receiver_id'],
                                      USER_PRV_KEY,
                                      rtip_desc['id'],
                                      'message')

        self.dummyWBTips = yield self.get_wbtips()

        for wbtip_desc in self.dummyWBTips:
            yield wbtip.create_comment(1,
                                       wbtip_desc['id'],
                                       USER_PRV_KEY,
                                       'comment')

            for receiver_id in wbtip_desc['receivers_ids']:
                yield wbtip.create_message(1,
                                           wbtip_desc['id'],
                                           USER_PRV_KEY,
                                           receiver_id,
                                           'message')

    @inlineCallbacks
    def perform_full_submission_actions(self):
        """Populates the DB with tips, comments, messages and files"""
        for x in range(self.population_of_submissions):
            token = self.perform_submission_start()
            self.perform_submission_uploads(token)
            yield self.perform_submission_actions(token)

        yield self.perform_post_submission_actions()

        yield self.test_model_count(models.SecureFileDelete, 0)

    @inlineCallbacks
    def perform_minimal_submission(self):
        token = self.perform_submission_start()
        self.perform_submission_uploads(token)
        yield self.perform_submission_actions(token)

    @transact
    def force_wbtip_expiration(self, session):
        session.query(models.InternalTip).update({'wb_last_access': datetime_null()})

    @transact
    def force_itip_expiration(self, session):
        session.query(models.InternalTip).update({'expiration_date': datetime_null()})

    @transact
    def set_itips_near_to_expire(self, session):
        date = datetime_now() + timedelta(hours=self.state.tenant_cache[1].notification.tip_expiration_threshold - 1)
        session.query(models.InternalTip).update({'expiration_date': date})

    @transact
    def set_contexts_timetolive(self, session, ttl):
        session.query(models.Context).update({'tip_timetolive': ttl})

    @transact
    def set_passwords_ready_to_expire(self, session, tid):
        session.query(models.User) \
            .filter(models.User.tid == tid) \
            .update({
                'password_change_date': datetime_null(),
                'password_change_needed': False,
            })


class TestHandler(TestGLWithPopulatedDB):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None
    _test_desc = {}
    # _test_desc = {
    #  'model': Context
    #  'create': context.create_context
    #  'data': {
    #
    #  }
    # }

    def setUp(self):
        return TestGL.setUp(self)

    def request(self, body='', uri=b'https://www.globaleaks.org/',
                user_id=None, role=None, multilang=False, headers=None,
                client_addr=None, handler_cls=None, attached_file=None,
                kwargs={}):
        """
        Constructs a handler for preforming mock requests using the bag of params described below.
        """
        from globaleaks.rest import api

        if handler_cls is None:
            handler_cls = self._handler

        request = forge_request(uri=uri,
                                headers=headers,
                                body=body,
                                client_addr=client_addr,
                                method=b'GET')

        x = api.APIResourceWrapper()
        x.preprocess(request)

        if not getattr(handler_cls, 'decorated', False):
            for method in ['get', 'post', 'put', 'delete']:
                if getattr(handler_cls, method, None) is not None:
                    decorators.decorate_method(handler_cls, method)
                    handler_cls.decorated = True

        handler = handler_cls(self.state, request, **kwargs)

        if multilang:
            request.language = None

        if user_id is None and role is not None:
            if role == 'admin':
                user_id = self.dummyAdminUser['id']
            elif role == 'receiver':
                user_id = self.dummyReceiverUser_1['id']
            elif role == 'custodian':
                user_id = self.dummyCustodianUser['id']

        if headers is not None and headers.get('x-session', None) is not None:
            handler.request.headers[b'x-session'] = headers.get('x-session').encode()

        elif role is not None:
            session = Sessions.new(1, user_id, role, False, USER_PRV_KEY)
            handler.request.headers[b'x-session'] = session.id.encode()

        if handler.upload_handler:
            handler.uploaded_file = self.get_dummy_file(u'upload.raw', attached_file)

        return handler

    def ss_serial_desc(self, safe_set, request_desc):
        """
        Constructs a request_dec parser of a handler that uses a safe_set in its serialization
        """
        return {k: v for k, v in request_desc.items() if k in safe_set}

    def get_dummy_request(self):
        return self._test_desc['model']().dict(u'en')


class TestCollectionHandler(TestHandler):
    @inlineCallbacks
    def test_get(self):
        if not self._test_desc:
            return

        data = self.get_dummy_request()

        yield self._test_desc['create'](1, data, u'en')

        handler = self.request(role='admin')

        if hasattr(handler, 'get'):
            yield handler.get()

    @inlineCallbacks
    def test_post(self):
        if not self._test_desc:
            return

        data = self.get_dummy_request()

        for k, v in self._test_desc['data'].items():
            self.assertNotEqual(data[k], v)
            data[k] = v

        handler = self.request(data, role='admin')

        if hasattr(handler, 'post'):
            data = yield handler.post()

            for k, v in self._test_desc['data'].items():
                self.assertTrue(data[k], v)


class TestInstanceHandler(TestHandler):
    @inlineCallbacks
    def test_get(self):
        if not self._test_desc:
            return

        data = self.get_dummy_request()

        data = yield self._test_desc['create'](1, data, u'en')

        handler = self.request(data, role='admin')

        if hasattr(handler, 'get'):
            yield handler.get(data['id'])

    @inlineCallbacks
    def test_put(self):
        if not self._test_desc:
            return

        data = self.get_dummy_request()

        data = yield self._test_desc['create'](1, data, u'en')

        for k, v in self._test_desc['data'].items():
            data[k] = v

        handler = self.request(data, role='admin')

        if hasattr(handler, 'put'):
            data = yield handler.put(data['id'])

            for k, v in self._test_desc['data'].items():
                self.assertEqual(data[k], v)

    @inlineCallbacks
    def test_delete(self):
        if not self._test_desc:
            return

        data = self.get_dummy_request()

        data = yield self._test_desc['create'](1, data, u'en')

        handler = self.request(data, role='admin')

        if hasattr(handler, 'delete'):
            yield handler.delete(data['id'])


class TestHandlerWithPopulatedDB(TestHandler):
    def setUp(self):
        return TestGLWithPopulatedDB.setUp(self)


class MockDict:
    """
    This class just create all the shit we need for emulate a Node
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
            'description': u'King MockDummy',
            'last_login': u'1970-01-01 00:00:00.000000',
            'language': u'en',
            'password_change_needed': False,
            'password_change_date': u'1970-01-01 00:00:00.000000',
            'pgp_key_fingerprint': u'',
            'pgp_key_public': u'',
            'pgp_key_expiration': u'1970-01-01 00:00:00.000000',
            'pgp_key_remove': False,
            'can_edit_general_settings': False,
            'notification': True
        }

        self.dummyReceiver = copy.deepcopy(self.dummyUser)

        self.dummyReceiver = sum_dicts(self.dummyReceiver, {
            'can_delete_submission': True,
            'can_postpone_expiration': True,
            'contexts': [],
            'configuration': 'default'
        })

        self.dummyContext = {
            'id': '',
            'name': u'Already localized name',
            'description': u'Already localized desc',
            'recipients_clarification': u'',
            'presentation_order': 0,
            'receivers': [],
            'questionnaire_id': u'default',
            'additional_questionnaire_id': '',
            'select_all_receivers': True,
            'tip_timetolive': 20,
            'maximum_selectable_receivers': 0,
            'show_small_receiver_cards': False,
            'show_context': True,
            'show_recipients_details': True,
            'allow_recipients_selection': False,
            'enable_comments': True,
            'enable_messages': True,
            'enable_two_way_comments': True,
            'enable_two_way_messages': True,
            'enable_attachments': True,
            'enable_rc_to_wb_files': True,
            'show_receivers_in_alphabetical_order': False,
            'status_page_message': ''
        }

        self.dummySubmission = {
            'context_id': '',
            'answers': {},
            'receivers': [],
            'files': []
        }

        self.dummyNode = {
            'name': u'Please, set me: name/title',
            'description': u'Pleæs€, set m€: d€scription',
            'presentation': u'This is whæt æpp€ærs on top',
            'footer': u'check it out https://www.youtube.com/franksentus ;)',
            'enable_disclaimer': False,
            'disclaimer_title': u'',
            'disclaimer_text': u'',
            'whistleblowing_question': u'',
            'whistleblowing_button': u'',
            'whistleblowing_receipt_prompt': u'',
            'hostname': u'www.globaleaks.org',
            'onionservice': u'',
            'rootdomain': u'antani.gov',
            'tb_download_link': u'https://www.torproject.org/download/download',
            'email': u'email@dummy.net',
            'languages_supported': [],  # ignored
            'languages_enabled': ['it', 'en'],
            'latest_version': __version__,
            'receipt_salt': '<<the Lannisters send their regards>>',
            'maximum_filesize': 30,
            'https_admin': True,
            'https_custodian': True,
            'https_whistleblower': True,
            'https_receiver': True,
            'can_postpone_expiration': False,
            'can_delete_submission': False,
            'can_grant_permissions': False,
            'ahmia': False,
            'allow_indexing': False,
            'allow_unencrypted': True,
            'allow_iframes_inclusion': False,
            'custom_homepage': False,
            'disable_submissions': False,
            'disable_privacy_badge': False,
            'disable_key_code_hint': False,
            'disable_donation_panel': False,
            'default_language': u'en',
            'default_password': u'globaleaks',
            'default_questionnaire': u'default',
            'admin_language': u'en',
            'multisite_login': False,
            'simplified_login': False,
            'enable_experimental_features': False,
            'enable_signup': True,
            'mode': u'default',
            'signup_tos1_enable': False,
            'signup_tos1_title': u'',
            'signup_tos1_text': u'',
            'signup_tos1_checkbox_label': u'',
            'signup_tos2_enable': False,
            'signup_tos2_title': u'',
            'signup_tos2_text': u'',
            'signup_tos2_checkbox_label': u'',
            'enable_graphic_customization': True,
            'enable_footer_customization': False,
            'enable_custom_privacy_badge': False,
            'custom_privacy_badge_text': u'',
            'header_title_homepage': u'',
            'header_title_submissionpage': u'',
            'header_title_receiptpage': u'',
            'header_title_tippage': u'',
            'landing_page': u'homepage',
            'context_selector_type': u'list',
            'contexts_clarification': u'',
            'show_contexts_in_alphabetical_order': False,
            'show_small_context_cards': False,
            'widget_comments_title': '',
            'widget_messages_title': '',
            'widget_files_title': '',
            'threshold_free_disk_megabytes_high': 200,
            'threshold_free_disk_megabytes_low': 1000,
            'threshold_free_disk_percentage_high': 3,
            'threshold_free_disk_percentage_low': 10,
            'password_change_period': 90,
            'wbtip_timetolive': 90,
            'basic_auth': False,
            'basic_auth_username': '',
            'basic_auth_password': '',
            'reachable_via_web': False,
            'anonymize_outgoing_connections': False,
            'enable_admin_exception_notification': True,
            'enable_developers_exception_notification': True,
            'ip_filter_admin': u'',
            'ip_filter_admin_enable': False,
            'ip_filter_custodian': u'',
            'ip_filter_custodian_enable': False,
            'ip_filter_receiver': u'',
            'ip_filter_receiver_enable': False,
            'ip_filter_whistleblower': u'',
            'ip_filter_whistleblower_enable': False,
            'counter_submissions': 0,
            'enable_password_reset': True,
            'enable_user_pgp_key_upload': False,
            'log_level': 'DEBUG',
            'log_accesses_of_internal_users': False,
            'encryption': False,
            'two_factor_auth': False,
            'multisite': False,
            'backup': False,
            'backup_d': 3,
            'backup_w': 3,
            'backup_m': 3,
            'backup_remote': False,
            'backup_remote_server': u'',
            'backup_remote_port': 22,
            'backup_remote_username': u'',
            'backup_remote_password': u''
        }


class SimpleServerPP(ProcessProtocol):
    def __init__(self):
        self.welcome_msg = False
        self.start_defer = Deferred()
        process.set_pdeathsig(signal.SIGTERM)

    def outReceived(self, data):
        # When the HTTPServer is ready it will produce a msg which we can hook
        # the start_defer callback to.
        if not self.welcome_msg:
            self.start_defer.callback(None)
            self.welcome_msg = True
