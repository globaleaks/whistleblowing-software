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
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.trial import unittest
from twisted.test import proto_helpers

from globaleaks import db, models, security, anomaly
from globaleaks.db.datainit import opportunistic_appdata_init, import_memory_variables
from globaleaks.handlers import files, rtip, wbtip, authentication
from globaleaks.handlers.base import GLApiCache
from globaleaks.handlers.admin import create_context, update_context, create_receiver, db_get_context_steps
from globaleaks.handlers.admin.field import create_field
from globaleaks.handlers.submission import create_submission, update_submission, create_whistleblower_tip
from globaleaks.jobs import delivery_sched, notification_sched, statistics_sched
from globaleaks.models import db_forge_obj, ReceiverTip, ReceiverFile, WhistleblowerTip, InternalTip
from globaleaks.plugins import notification
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.utils import mailutils
from globaleaks.utils.utility import datetime_null, uuid4, log
from globaleaks.third_party import rstr
from globaleaks.security import GLSecureTemporaryFile

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


with open(os.path.join(TEST_DIR, 'valid_pgp_key.txt')) as pgp_file:
    VALID_PGP_KEY = pgp_file.read()

transact.tp = FakeThreadPool()
authentication.reactor = task.Clock()
anomaly.reactor = task.Clock()
anomaly.notification = False

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
            mock_class = getattr(models, mock['class'])
            db_forge_obj(store, mock_class, mock['fields'])


class TestGL(unittest.TestCase):

    encryption_scenario = 'MIXED' # receivers with pgp and receivers without pgp

    @inlineCallbacks
    def setUp(self, create_node=True):
        GLSetting.set_devel_mode()
        GLSetting.logging = None
        GLSetting.scheduler_threadpool = FakeThreadPool()
        GLSetting.memory_copy.allow_unencrypted = True
        GLSetting.sessions = {}
        GLSetting.failed_login_attempts = 0
        GLSetting.working_path = './working_path'
        GLSetting.ramdisk_path = './working_path/ramdisk'

        GLSetting.eval_paths()
        GLSetting.remove_directories()
        GLSetting.create_directories()

        self.setUp_dummy()

        # This mocks out the MailNotification plugin so it does not actually
        # require to perform a connection to send an email.
        # XXX we probably want to create a proper mock of the ESMTPSenderFactory
        def mail_flush_mock(self, from_address, to_address, message_file, event):
            return defer.succeed(None)

        notification.MailNotification.mail_flush = mail_flush_mock

        yield db.create_tables(create_node)

        for fixture in getattr(self, 'fixtures', []):
            yield import_fixture(fixture)

        import_memory_variables()

        anomaly.Alarm.reset()
        anomaly.EventTrackQueue.reset()
        statistics_sched.StatisticsSchedule.reset()

    def setUp_dummy(self):
        dummyStuff = MockDict()

        self.dummyFields = dummyStuff.dummyFields
        self.dummyFieldTemplates = dummyStuff.dummyFieldTemplates
        self.dummyContext = dummyStuff.dummyContext
        self.dummySubmission = dummyStuff.dummySubmission
        self.dummyNotification = dummyStuff.dummyNotification
        self.dummyReceiverUser_1 = self.get_dummy_receiver_user('receiver1')
        self.dummyReceiverUser_2 = self.get_dummy_receiver_user('receiver2')
        self.dummyReceiver_1 = self.get_dummy_receiver('receiver1') # the one without PGP
        self.dummyReceiver_2 = self.get_dummy_receiver('receiver2') # the one with PGP

        if self.encryption_scenario == 'MIXED':
            self.dummyReceiver_1['gpg_key_armor'] = None
            self.dummyReceiver_2['gpg_key_armor'] = VALID_PGP_KEY
        elif self.encryption_scenario == 'ALL_ENCRYPTED':
            self.dummyReceiver_1['gpg_key_armor'] = VALID_PGP_KEY
            self.dummyReceiver_2['gpg_key_armor'] = VALID_PGP_KEY
        elif self.encryption_scenario == 'ALL_PLAINTEXT':
            self.dummyReceiver_1['gpg_key_armor'] = None
            self.dummyReceiver_2['gpg_key_armor'] = None

        self.dummyNode = dummyStuff.dummyNode

        self.assertEqual(os.listdir(GLSetting.submission_path),  [])
        self.assertEqual(os.listdir(GLSetting.tmp_upload_path), [])

    def localization_set(self, dict_l, dict_c, language):
        ret = dict(dict_l)

        for attr in getattr(dict_c, 'localized_strings'):
            ret[attr] = {}
            ret[attr][language] = unicode(dict_l[attr])

        return ret

    def get_dummy_receiver_user(self, descpattern):
        new_ru = dict(MockDict().dummyReceiverUser)
        new_ru['username'] = unicode("%s@%s.xxx" % (descpattern, descpattern))
        return new_ru

    def get_dummy_receiver(self, descpattern):
        new_r = dict(MockDict().dummyReceiver)
        new_r['name'] = new_r['username'] =\
        new_r['mail_address'] = unicode('%s@%s.xxx' % (descpattern, descpattern))
        new_r['password'] = VALID_PASSWORD1
        # localized dict required in desc
        new_r['description'] =  'am I ignored ? %s' % descpattern
        return new_r

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
        dummySubmissionDict['wb_steps'] = yield fill_random_fields(context_id)
        dummySubmissionDict['receivers'] = []
        dummySubmissionDict['files'] = []
        dummySubmissionDict['finalize'] = True

        defer.returnValue(dummySubmissionDict)

    def get_dummy_file(self, filename=None, content_type=None, content=None):

        if filename is None:
            filename = ''.join(unichr(x) for x in range(0x400, 0x40A))

        if content_type is None:
            content_type = 'application/octet'

        if content is None:
            content = 'ANTANI'

        temporary_file = GLSecureTemporaryFile(GLSetting.tmp_upload_path)

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
    def emulate_file_upload(self, associated_submission_id):

        for i in range(0,2): # we emulate a constant upload of 2 files

            dummyFile = self.get_dummy_file()

            relationship = yield threads.deferToThread(files.dump_file_fs, dummyFile)
            registered_file = yield files.register_file_db(
                dummyFile, relationship, associated_submission_id,
            )

            self.assertFalse({'size', 'content_type', 'name', 'creation_date', 'id'} - set(registered_file.keys()))

    @transact_ro
    def _exists(self, store, model, *id_args, **id_kwargs):
        if not id_args and not id_kwargs:
            raise ValueError
        return model.get(store, *id_args, **id_kwargs) is not None

    @inlineCallbacks
    def assert_model_exists(self, model, *id_args, **id_kwargs):
        existing = yield self._exists(model, *id_args, **id_kwargs)
        msg =  'The following has *NOT* been found on the store: {} {}'.format(id_args, id_kwargs)
        self.assertTrue(existing, msg)

    @inlineCallbacks
    def assert_model_not_exists(self, model, *id_args, **id_kwargs):
        existing = yield self._exists(model, *id_args, **id_kwargs)
        msg =  'The following model has been found on the store: {} {}'.format(id_args, id_kwargs)
        self.assertFalse(existing, msg)

    @transact_ro
    def get_finalized_submissions_ids(self, store):
        ids = []
        submissions = store.find(InternalTip, InternalTip.mark != u'submission')
        for s in submissions:
            ids.append(s.id)

        return ids

    @transact_ro
    def get_rtips(self, store):
        rtips_desc = []
        rtips = store.find(ReceiverTip)
        for rtip in rtips:
            rtips_desc.append({'rtip_id': rtip.id, 'receiver_id': rtip.receiver_id})

        return rtips_desc

    @transact_ro
    def get_rfiles(self, store, rtip_id):
        rfiles_desc = []
        rfiles = store.find(ReceiverFile, ReceiverFile.receiver_tip_id == rtip_id)
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
            wbtips_desc.append({'wbtip_id': wbtip.id, 'wbtip_receivers': rcvrs_ids})

        return wbtips_desc


class TestGLWithPopulatedDB(TestGL):

    @inlineCallbacks
    def setUp(self):
        yield TestGL.setUp(self)
        yield self.fill_data()

    def receiver_assertion(self, source_r, created_r):
        self.assertEqual(source_r['name'], created_r['name'], 'name')
        self.assertEqual(source_r['can_delete_submission'], created_r['can_delete_submission'], 'delete')

    def context_assertion(self, source_c, created_c):
        self.assertEqual(source_c['tip_max_access'], created_c['tip_max_access'])

    @transact_ro
    def get_rtips(self, store):
        rtips_desc = []
        rtips = store.find(ReceiverTip)
        for rtip in rtips:
            rtips_desc.append({'rtip_id': rtip.id, 'receiver_id': rtip.receiver_id})

        return rtips_desc

    @transact_ro
    def get_wbtips(self, store):
        wbtips_desc = []
        wbtips = store.find(WhistleblowerTip)
        for wbtip in wbtips:
            rcvrs_ids = []
            for rcvr in wbtip.internaltip.receivers:
                rcvrs_ids.append(rcvr.id)
            wbtips_desc.append({'wbtip_id': wbtip.id, 'wbtip_receivers': rcvrs_ids})

        return wbtips_desc

    @inlineCallbacks
    def fill_data(self):
        yield do_appdata_init()

        receivers_ids = []

        # fill_data/create_receiver
        self.dummyReceiver_1 = yield create_receiver(self.dummyReceiver_1)
        receivers_ids.append(self.dummyReceiver_1['id'])
        self.dummyReceiver_2 = yield create_receiver(self.dummyReceiver_2)
        receivers_ids.append(self.dummyReceiver_2['id'])

        # fill_data/create_context
        self.dummyContext['receivers'] = receivers_ids
        self.dummyContext = yield create_context(self.dummyContext)

        # fill_data: create cield templates
        for idx, field in enumerate(self.dummyFieldTemplates):
            f = yield create_field(field, 'en')
            self.dummyFieldTemplates[idx]['id'] = f['id']

        # fill_data: create fields and associate them to the context steps
        for idx, field in enumerate(self.dummyFields):
            field['is_template'] = False
            if idx <= 2:
                # "Field 1", "Field 2" and "Generalities" are associated to the first step
                field['step_id'] = self.dummyContext['steps'][0]['id']
            else:
                # Name, Surname, Gender" are associated to field "Generalities"
                # "Field 1" and "Field 2" are associated to the first step
                field['fieldgroup_id'] = self.dummyFields[2]['id']
               
            f = yield create_field(field, 'en')
            self.dummyFields[idx]['id'] = f['id']

        self.dummyContext['steps'][0]['children'] = [
            self.dummyFields[0]['id'], # Field 1
            self.dummyFields[1]['id'], # Field 2
            self.dummyFields[2]['id']  # Generalities
        ]

        yield update_context(self.dummyContext['id'], self.dummyContext)

        # fill_data/create_submission
        self.dummySubmission['context_id'] = self.dummyContext['id']
        self.dummySubmission['receivers'] = receivers_ids
        self.dummySubmission['wb_steps'] = yield fill_random_fields(self.dummyContext['id'])
        self.dummySubmissionNotFinalized = yield create_submission(self.dummySubmission, finalize=False)
        self.dummySubmission = yield create_submission(self.dummySubmission, finalize=False)

        yield self.emulate_file_upload(self.dummySubmission['id'])
        # fill_data/update_submssion
        submission = yield update_submission(self.dummySubmission['id'], self.dummySubmission, finalize=True)
        # fill_data/create_whistleblower
        self.dummyWBTip = yield create_whistleblower_tip(self.dummySubmission)

        assert self.dummyReceiver_1.has_key('id')
        assert self.dummyReceiver_2.has_key('id')
        assert self.dummyContext.has_key('id')
        assert self.dummySubmission.has_key('id')

        yield delivery_sched.DeliverySchedule().operation()
        yield notification_sched.NotificationSchedule().operation()

        commentCreation = {
            'content': 'comment!',
        }

        messageCreation = {
            'content': 'message!',
        }

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            yield rtip.create_comment_receiver(rtip_desc['receiver_id'],
                                               rtip_desc['rtip_id'],
                                               commentCreation)

            yield rtip.create_message_receiver(rtip_desc['receiver_id'],
                                               rtip_desc['rtip_id'],
                                               messageCreation)


        wbtips_desc = yield self.get_wbtips()

        for wbtip_desc in wbtips_desc:
            yield wbtip.create_comment_wb(wbtip_desc['wbtip_id'],
                                          commentCreation)

            for receiver_id in wbtip_desc['wbtip_receivers']:
                yield wbtip.create_message_wb(wbtip_desc['wbtip_id'], receiver_id, messageCreation)

        yield delivery_sched.DeliverySchedule().operation()
        yield notification_sched.NotificationSchedule().operation()



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
            if response:
                self.responses.append(response)

        self._handler.write = mock_write
        # we make the assumption that we will always use call finish on write.
        self._handler.finish = mock_write

        # we need to reset settings.session to keep each test independent
        GLSetting.sessions = dict()

        # we need to reset GLApiCache to keep each test independent
        GLApiCache.invalidate()

    def request(self, jbody=None, role=None, user_id=None, headers=None, body='',
                remote_ip='0.0.0.0', method='MOCK', kwargs={}):

        """
        Function userful for performing mock requests.

        Args:

            jbody:
                The body of the request as a dict (it will be automatically
                converted to string)

            body:
                The body of the request as a string

            role:
                If we should perform authentication role can be either "admin",
                "receiver" or "wb"

            user_id:
                If when performing authentication the session should be bound
                to a certain user_id.

            method:
                HTTP method, e.g. "GET" or "POST"

            uri:
                URL to fetch

            role:
                the role

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
        connection = httpserver.HTTPConnection()
        connection.factory = application
        connection.makeConnection(tr)

        request = httpserver.HTTPRequest(uri='mock',
                                         method=method,
                                         headers=headers,
                                         body=body,
                                         remote_ip=remote_ip,
                                         connection=connection)

        handler = self._handler(application, request, **kwargs)

        def mock_pass(cls, *args):
            pass
        # so that we don't complain about XSRF
        handler.check_xsrf_cookie = mock_pass

        if role:
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

        self.dummyReceiverUser = {
            'username': u'maker@iz.cool.yeah',
            'password': VALID_HASH1,
            'salt': VALID_SALT1,
            'role': u'receiver',
            'state': u'enabled',
            'last_login': datetime_null(),
            'timezone': 0,
            'language': u'en'
        }

        self.dummyReceiver = {
            'password': VALID_PASSWORD1,
            'name': u'Ned Stark',
            'description': u'King MockDummy Receiver',
            # Email can be different from the user, but at the creation time is used
            # the same address, therefore we keep the same of dummyReceiver.username
            'mail_address': self.dummyReceiverUser['username'],
            'can_delete_submission': True,
            'postpone_superpower': False,
            'receiver_level': 1,
            'contexts' : [],
            'tags': [ u'first', u'second', u'third' ],
            'tip_notification': True,
            'file_notification': True,
            'comment_notification': True,
            'message_notification': True,
            'gpg_key_info': u'',
            'gpg_key_fingerprint' : u'',
            'gpg_key_status': models.Receiver._gpg_types[0], # disabled
            'gpg_key_armor' : u'',
            'gpg_enable_notification': False,
            'gpg_key_remove': False,
            'presentation_order': 0,
            'timezone': 0,
            'language': u'en'
        }

        self.dummyFieldTemplates = [{
            'id': u'd4f06ad1-eb7a-4b0d-984f-09373520cce7',
            'is_template': True,
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'Field 1',
            'type': u'inputbox',
            'preview': False,
            'description': u"field description",
            'hint': u'field hint',
            'multi_entry': False,
            'stats_enabled': False,
            'required': True, # <- first field is special,
            'children': {},   #    it's marked as required!!!
            'options': [],
            'y': 2,
            'x': 0
            },
            {
            'id': u'c4572574-6e6b-4d86-9a2a-ba2e9221467d',
            'is_template': True,
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'Field 2',
            'type': u'inputbox',
            'preview': False,
            'description': "description",
            'hint': u'field hint',
            'multi_entry': False,
            'stats_enabled': False,
            'required': False,
            'children': {},
            'options': [],
            'y': 3,
            'x': 0
            },
            {
            'id': u'6a6e9282-15e8-47cd-9cc6-35fd40a4a58f',
            'is_template': True,
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'Generalities',
            'type': u'fieldgroup',
            'preview': False,
            'description': u"field description",
            'hint': u'field hint',
            'multi_entry': False,
            'stats_enabled': False,
            'required': False,
            'children': {},
            'options': [],
            'y': 4,
            'x': 0
            },
            {
            'id': u'7459abe3-52c9-4a7a-8d48-cabe3ffd2abd',
            'is_template': True,
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'Name',
            'type': u'inputbox',
            'preview': False,
            'description': u"field description",
            'hint': u'field hint',
            'multi_entry': False,
            'stats_enabled': False,
            'required': False,
            'children': {},
            'options': [],
            'y': 0,
            'x': 0
            },
            {
            'id': u'de1f0cf8-63a7-4ed8-bc5d-7cf0e5a2aec2',
            'is_template': True,
            'step_id': '',
            'fieldgroup_id': '',
            'label': u'Surname',
            'type': u'inputbox',
            'preview': False,
            'description': u"field description",
            'hint': u'field hint',
            'multi_entry': False,
            'stats_enabled': False,
            'required': False,
            'children': {},
            'options': [],
            'y': 0,
            'x': 0
            }]

        self.dummyFields = copy.deepcopy(self.dummyFieldTemplates)

        self.dummySteps = [{
            'label': u'Step 1',
            'description': u'Step Description',
            'hint': u'Step Hint',
            'children': {}
            },
            {
              'label': u'Step 2',
              'description': u'Step Description',
              'hint': u'Step Hint',
              'children': {}
            }]

        self.dummyContext = {
            # localized stuff
            'name': u'Already localized name',
            'description': u'Already localized desc',
            'steps': self.dummySteps,
            'selectable_receiver': False,
            'select_all_receivers': True,
            'tip_max_access': 10,
            # tip_timetolive is expressed in days
            'tip_timetolive': 20,
            # submission_timetolive is expressed in hours
            'submission_timetolive': 48,
            'file_max_download' :1,
            'escalation_threshold': 1,
            'receivers' : [],
            'tags': [],
            'file_required': False,
            'receiver_introduction': u'These are our receivers',
            'postpone_superpower': False,
            'can_delete_submission': False,
            'maximum_selectable_receivers': 0,
            'require_file_description': False,
            'delete_consensus_percentage': 0,
            'require_pgp': False,
            'show_small_cards': False,
            'show_receivers': False,
            'enable_private_messages': True,
            'presentation_order': 0,
        }

        self.dummySubmission = {
            'context_id': '',
            'wb_steps': [],
            'finalize': False,
            'receivers': [],
            'files': [],
        }

        self.dummyNode = {
            'name':  u"Please, set me: name/title",
            'description': u"Pleæs€, set m€: d€scription",
            'presentation': u'This is whæt æpp€ærs on top',
            'footer': u'check it out https://www.youtube.com/franksentus ;)',
            'subtitle': u'https://twitter.com/TheHackersNews/status/410457372042092544/photo/1',
            'terms_and_conditions': u'',
            'security_awareness_title': u'',
            'security_awareness_text': u'',
            'whistleblowing_question': u'',
            'whistleblowing_button': u'',
            'hidden_service':  u"http://1234567890123456.onion",
            'public_site':  u"https://globaleaks.org",
            'email':  u"email@dummy.net",
            'stats_update_time':  2, # hours,
            'languages_supported': [], # ignored
            'languages_enabled':  [ "it" , "en" ],
            'default_language': 'en',
            'password': '',
            'old_password': '',
            'salt': 'OMG!, the Rains of Castamere ;( ;(',
            'salt_receipt': '<<the Lannisters send their regards>>',
            'maximum_filesize': GLSetting.defaults.maximum_filesize,
            'maximum_namesize': GLSetting.defaults.maximum_namesize,
            'maximum_textsize': GLSetting.defaults.maximum_textsize,
            'tor2web_admin': True,
            'tor2web_submission': True,
            'tor2web_receiver': True,
            'tor2web_unauth': True,
            'postpone_superpower': False,
            'can_delete_submission': False,
            'exception_email': GLSetting.defaults.exception_email,
            'reset_css': False,
            'reset_homepage': False,
            'ahmia': False,
            'anomaly_checks': False,
            'allow_unencrypted': True,
            'configured': False,
            'wizard_done': False,
            'custom_homepage': False,
            'disable_privacy_badge': False,
            'disable_security_awareness_badge': False,
            'disable_security_awareness_questions': False,
            'default_timezone': 0,
            'default_language': u'en',
            'admin_timezone': 0,
            'admin_language': u'en',
            'enable_custom_privacy_badge': False,
            'custom_privacy_badge_tbb': u'',
            'custom_privacy_badge_tor': u'',
            'custom_privacy_badge_none': u'',
        }

        self.generic_template_keywords = [ '%NodeName%', '%HiddenService%',
                                           '%PublicSite%', '%ReceiverName%',
                                           '%ContextName%' ]
        self.tip_template_keywords = [ '%TipTorURL%', '%TipT2WURL%', '%EventTime%' ]
        self.comment_template_keywords = [ '%CommentSource%', '%EventTime%' ]
        self.file_template_keywords = [ '%FileName%', '%EventTime%',
                                        '%FileSize%', '%FileType%' ]

        self.dummyNotification = {
            'server': u'mail.foobar.xxx',
            'port': 12345,
            'username': u'xxxx@xxx.y',
            'password': u'antani',
            'security': u'SSL',
            'source_name': u'UnitTest Helper Name',
            'source_email': u'unit@test.help',
            'encrypted_tip_template': template_keys(self.tip_template_keywords,
                                          self.generic_template_keywords, "Tip"),
            'plaintext_tip_template': template_keys(self.tip_template_keywords,
                                                    self.generic_template_keywords, "Tip"),
            'encrypted_tip_mail_title': u'xXx',
            'plaintext_tip_mail_title': u'XxX',
            'encrypted_file_template':template_keys(self.file_template_keywords,
                                          self.generic_template_keywords, "File"),
            'plaintext_file_template':template_keys(self.file_template_keywords,
                                          self.generic_template_keywords, "File"),
            'encrypted_file_mail_title': u'kkk',
            'plaintext_file_mail_title': u'kkk',
            'encrypted_comment_template': template_keys(self.comment_template_keywords,
                                              self.generic_template_keywords, "Comment"),
            'plaintext_comment_template': template_keys(self.comment_template_keywords,
                                              self.generic_template_keywords, "Comment"),
            'encrypted_comment_mail_title': u'yyy',
            'plaintext_comment_mail_title': u'yyy',
            'encrypted_message_template': u'%B EventTime% %TipUN%',
            'plaintext_message_template': u'%B EventTime% %TipUN%',
            'encrypted_message_mail_title': u'T %EventTime %TipUN',
            'plaintext_message_mail_title': u'T %EventTime %TipUN',
            'zip_description': u'TODO',
            'disable': False,
        }


def template_keys(first_a, second_a, name):

    ret_string = '[{}]'.format(name)
    for x in first_a:
        ret_string += ' {}'.format(x)

    ret_string += ' == '

    for x in second_a:
        ret_string += ' {}'.format(x)

    return ret_string

def fill_random_field_recursively(field, value=None):
    if value is None:
        field['value'] = unicode(''.join(unichr(x) for x in range(0x400, 0x4FF)))
    else:
        field['value'] = unicode(value)

    for c in field['children']:
        fill_random_field_recursively(field['children'][c])

@transact
def fill_random_fields(store, context_id, value=None):
    """
    return randomly populated contexts associated to specified context
    """
    steps = db_get_context_steps(store, context_id)

    for step in steps:
        for field in step['children']:
            fill_random_field_recursively(step['children'][field])

    return steps

@transact
def do_appdata_init(store):
    try:
        appdata = store.find(models.ApplicationData).one()

        if not appdata:
            raise Exception

    except Exception as xxx:
        appdata = models.ApplicationData()
        source = opportunistic_appdata_init()
        appdata.version = source['version']
        appdata.fields = source['fields']
        store.add(appdata)

@transact
def create_dummy_field(store, **custom_attrs):
    attrs = {
        'label': { "en": "test label" },
        'description': { "en": "test description" },
        'hint': { "en": "test hint" },
        "is_template": False,
        'multi_entry': False,
        'type': 'fieldgroup',
        'options': [],
        'required': False,
        'preview': False,
        'stats_enabled': True,
        'x': 0,
        'y': 0
    }
    attrs.update(custom_attrs)
    return models.Field.new(store, attrs).id
