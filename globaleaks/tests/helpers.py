# -*- coding: UTF-8

import os
import json
import uuid
import shutil

from io import BytesIO as StringIO
from cyclone import httpserver
from cyclone.web import Application
from cyclone.util import ObjectDict as OD
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.defer import inlineCallbacks
from Crypto import Random
from storm.twisted.testing import FakeThreadPool

from globaleaks.settings import GLSetting, transact
from globaleaks.handlers.admin import create_context, create_receiver
from globaleaks.handlers.submission import create_submission, create_whistleblower_tip
from globaleaks import db, models, security
from globaleaks.utils.utility import datetime_null, datetime_now
from globaleaks.utils.structures import Fields
from globaleaks.third_party import rstr
from globaleaks.db.datainit import opportunistic_appdata_init

from globaleaks.security import GLSecureTemporaryFile


Random.atfork()

VALID_PASSWORD1 = u'justapasswordwithaletterandanumberandbiggerthan8chars'
VALID_PASSWORD2 = u'justap455w0rdwithaletterandanumberandbiggerthan8chars'
VALID_SALT1 = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
VALID_SALT2 = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
VALID_HASH1 = security.hash_password(VALID_PASSWORD1, VALID_SALT1)
VALID_HASH2 = security.hash_password(VALID_PASSWORD2, VALID_SALT2)

INVALID_PASSWORD = u'antani'

transact.tp = FakeThreadPool()

class UTlog():

    @staticmethod
    def err(stuff):
        pass

    @staticmethod
    def debug(stuff):
        pass

from globaleaks.utils.utility import log
# I'm trying by feeling
log.err = UTlog().err
log.debug = UTlog().debug
# woha and it's working! I'm starting to thing like python want!

class TestWithDB(unittest.TestCase):
    def setUp(self):
        GLSetting.set_devel_mode()
        GLSetting.logging = None
        GLSetting.scheduler_threadpool = FakeThreadPool()
        GLSetting.sessions = {}
        GLSetting.failed_login_attempts = dict()
        GLSetting.failed_login_attempts_wb = 0
        GLSetting.working_path = os.path.abspath(os.path.join(GLSetting.root_path, 'testing_dir'))
        GLSetting.eval_paths()
        GLSetting.remove_directories()
        GLSetting.create_directories()
        GLSetting.load_key()
        GLSetting.cleaning_dead_files()

        return db.create_tables(create_node=True)

class TestGL(TestWithDB):

    @inlineCallbacks
    def _setUp(self):

        try:
            if not os.path.isdir('files'):
                log.debug("Creating directory 'files' in %s" % os.getcwd())
                os.mkdir('files')

            if not os.path.isdir('files/submission'):
                log.debug("Creating directory 'files/submission' in %s" % os.getcwd())
                os.mkdir('files/submission')

            if not os.path.isdir('ramdisk'):
                log.debug("Creating directory 'ramdisk' in %s" % os.getcwd())
                os.mkdir('ramdisk')

        except OSError as excep:
            log.err("Unable to setup disk emulation environment: %s" % excep.strerror)
            raise excep

        yield TestWithDB.setUp(self)
        self.setUp_dummy()
        yield self.fill_data()

    def setUp(self):
        return self._setUp()

    def setUp_dummy(self):

        dummyStuff = MockDict()

        self.dummyContext = dummyStuff.dummyContext
        self.dummySubmission = dummyStuff.dummySubmission
        self.dummyNotification = dummyStuff.dummyNotification
        self.dummyReceiverUser = dummyStuff.dummyReceiverUser
        self.dummyReceiver = dummyStuff.dummyReceiver
        self.dummyNode = dummyStuff.dummyNode

    def receiver_assertion(self, source_r, created_r):
        self.assertEqual(source_r['name'], created_r['name'], "name")
        self.assertEqual(source_r['can_delete_submission'], created_r['can_delete_submission'], "delete")
        self.assertEqual(source_r['gpg_enable_files'], created_r['gpg_enable_files'], "GPGf")

    def context_assertion(self, source_c, created_c):
        self.assertEqual(source_c['tip_max_access'], created_c['tip_max_access'])

    @inlineCallbacks
    def fill_data(self):

        try:
            yield do_appdata_init()

        except Exception as excp:
            print "Fail fill_data/do_appdata_init: %s" % excp
            raise  excp

        try:
            receiver = yield create_receiver(self.dummyReceiver)

            self.dummyReceiver['id'] = receiver['id']
            self.receiver_assertion(self.dummyReceiver, receiver)
        except Exception as excp:
            print "Fail fill_data/create_receiver: %s" % excp
            raise  excp

        try:
            self.dummyContext['receivers'] = [ self.dummyReceiver['id'] ]
            context = yield create_context(self.dummyContext)
            self.dummyContext['id'] = context['id']

        except Exception as excp:
            print "Fail fill_data/create_context: %s" % excp
            raise  excp

        self.dummySubmission['context_id'] = self.dummyContext['id']
        self.dummySubmission['receivers'] = [ self.dummyReceiver['id'] ]
        self.dummySubmission['wb_fields'] = fill_random_fields(self.dummyContext)

        try:
            submission = yield create_submission(self.dummySubmission, finalize=True)
            self.dummySubmission['id'] = submission['id']
        except Exception as excp:
            print "Fail fill_data/create_submission: %s" % excp
            raise  excp

        try:
            self.dummyWBTip = yield create_whistleblower_tip(self.dummySubmission)
        except Exception as excp:
            print "Fail fill_data/create_whistleblower: %s" % excp
            raise  excp

        assert self.dummyContext.has_key('id')
        assert self.dummyReceiver.has_key('id')
        assert self.dummySubmission.has_key('id')


    def localization_set(self, dict_l, dict_c, language):
        ret = dict(dict_l)

        for attr in getattr(dict_c, "localized_strings"):
            ret[attr] = {}
            ret[attr][language] = unicode(dict_l[attr])
        
        return ret

class TestHandler(TestGL):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    @inlineCallbacks
    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        yield TestGL.setUp(self)
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
            session_id = '4tehlulz'
            new_session = OD(
                   refreshdate=datetime_now(),
                   id=session_id,
                   role=role,
                   user_id=user_id
            )
            GLSetting.sessions[session_id] = new_session
            handler.request.headers['X-Session'] = session_id
        return handler


class MockDict():
    """
    This class just create all the shit we need for emulate a GLNode
    """

    def __init__(self):

        self.dummyReceiverUser = {
            'username': u'maker@iz.cool.yeah',
            'password': VALID_HASH1,
            'salt': VALID_SALT1,
            'role': u'admin',
            'state': u'enabled',
            'last_login': datetime_null(),
            'failed_login_count': 0
        }

        self.dummyReceiver = {
            'id': unicode(uuid.uuid4()),
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
            'gpg_enable_files': False,
            'gpg_key_remove': False,
            'presentation_order': 0,
        }

        self.dummyContext = {
            'id': unicode(uuid.uuid4()),
            # localized stuff
            'name': u'Already localized name',
            'description': u'Already localized desc',
            # fields, usually filled in content by fill_random_fields
            'fields': default_context_fields(),
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
            'receipt_regexp': u'[A-Z]{4}\+[0-9]{5}',
            'file_required': False,
            'receiver_introduction': u'These are our receivers',
            'fields_introduction': u'These are our fields',
            'postpone_superpower': False,
            'can_delete_submission': False,
            'maximum_selectable_receivers': 0,
            'require_file_description': False,
            'delete_consensus_percentage': 0,
            'require_pgp': False,
            'show_small_cards': False,
            'presentation_order': 0,
        }

        self.dummySubmission = {
            'context_id': '',
            'wb_fields': fill_random_fields(self.dummyContext),
            'finalize': False,
            'receivers': [],
        }

        self.dummyNode = {
            'name':  u"Please, set me: name/title",
            'description': u"Pleæs€, set m€: d€scription",
            'presentation': u'This is whæt æpp€ærs on top',
            'footer': u'check it out https://www.youtube.com/franksentus ;)',
            'subtitle': u'https://twitter.com/TheHackersNews/status/410457372042092544/photo/1',
            'hidden_service':  u"http://1234567890123456.onion",
            'public_site':  u"https://globaleaks.org",
            'email':  u"email@dumnmy.net",
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
            'ahmia': False,
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
            'source_email': u'unit@test.helper',
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

        temporary_file = GLSecureTemporaryFile('files/submission')
        temporary_file.write("ANTANI")

        self.dummyFile = {
            'body': temporary_file,
            'body_len': len("ANTANI"),
            'body_sha': 'b1dc5f0ba862fe3a1608d985ded3c5ed6b9a7418db186d9e6e6201794f59ba54',
            'body_filepath': temporary_file.filepath,
            'filename': ''.join(unichr(x) for x in range(0x400, 0x40A)),
            'content_type': 'application/octect',
        }


def template_keys(first_a, second_a, name):

    ret_string = "[%s]" % name
    for x in first_a:
        ret_string += " %s" % x

    ret_string += " == "

    for x in second_a:
        ret_string += " %s" % x

    return ret_string

def get_dummy_submission(context_id, context_admin_data_fields):
    """
    this may works until the content of the fields do not start to be validated. like
    numbers shall contain only number, and not URL.
    This validation would not be implemented in validate_jmessage but in structures.Fields

    need to be enhanced generating appropriate data based on the fields.type
    """

    dummySubmissionDict = {}
    dummySubmissionDict['wb_fields'] = {}

    dummyvalue = "https://dailyfoodporn.wordpress.com && " \
                 "http://www.zerocalcare.it/ && " \
                 "http://www.giantitp.com"

    for field_desc in context_admin_data_fields:
        dummySubmissionDict['wb_fields'][field_desc['key']] = dummyvalue

    dummySubmissionDict['receivers'] = []
    dummySubmissionDict['files'] = []
    dummySubmissionDict['finalize'] = True
    dummySubmissionDict['context_id'] = context_id
    return dummySubmissionDict

def fill_random_fields(context_desc):
    """
    getting the context dict, take 'fields'.
    then populate a valid dict of key : value, usable as wb_fields
    """

    assert isinstance(context_desc, dict)
    fields_list = context_desc['fields']
    assert isinstance(fields_list, list), "Missing fields!"
    assert len(fields_list) >= 1

    ret_dict = {}
    for sf in fields_list:

        assert sf.has_key(u'name')
        assert sf.has_key(u'key')
        assert sf.has_key(u'hint')
        assert sf.has_key(u'presentation_order')
        assert sf.has_key(u'type')
        # not all element are checked now

        unicode_weird = ''.join(unichr(x) for x in range(0x400, 0x4FF) )
        ret_dict.update({ sf.get(u'key') : unicode_weird })

    return ret_dict


def default_context_fields():

    source = opportunistic_appdata_init()
    if not source.has_key('fields'):
        raise Exception("Invalid Application Data initialization")

    f = source['fields']
    fo = Fields()
    fo.noisy = True
    fo.default_fields(f)
    default_fields_unhappy = fo.dump_fields('en')

    ret_fields = []
    the_first_is_required = False

    for field in default_fields_unhappy:

        if not the_first_is_required:
            field['required'] = True
            the_first_is_required = True

        ret_fields.append(field)

    return ret_fields


@transact
def do_appdata_init(store):

    try:
        appdata = store.find(models.ApplicationData).one()

        if not appdata:
            raise Exception

    except Exception as xxx:
        appdata = models.ApplicationData()

        source = opportunistic_appdata_init()
        appdata.fields_version = source['version']
        appdata.fields = source['fields']

        store.add(appdata)

    fo = Fields()
    fo.noisy = True
    fo.default_fields(appdata.fields)
    (unique_fields, localized_fields) = fo.extensive_dump()

    return unique_fields, localized_fields


