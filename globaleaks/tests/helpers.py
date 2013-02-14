import os
import json

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.defer import inlineCallbacks
from storm.twisted.testing import FakeThreadPool
from storm.zope.zstorm import ZStorm
from cyclone.util import ObjectDict as OD
from cyclone import httpserver
from cyclone.web import Application

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin import create_context, create_receiver, update_node
from globaleaks.handlers.submission import create_submission, create_whistleblower_tip

from globaleaks.settings import transact
from globaleaks.rest import errors
from globaleaks import models
from globaleaks import settings
from globaleaks import db

_TEST_DB = 'test.db'
settings.db_file = 'sqlite:///' + _TEST_DB
settings.store = 'test_store'

import storm

class TestHandler(unittest.TestCase):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    @inlineCallbacks
    def fill_data(self):
        self.dummyReceiver = yield create_receiver(self.dummyReceiver)

        self.dummyContext['receivers'] = [self.dummyReceiver['receiver_gus']]
        context_dict = yield create_context(self.dummyContext)

        self.dummyReceiver['contexts'] = [context_dict['context_gus']]
        self.dummyContext['receivers'] = [self.dummyReceiver['receiver_gus']]
        self.dummyContext['context_gus'] = context_dict['context_gus']

        self.dummySubmission['context_gus'] = context_dict['context_gus']
        yield create_submission(self.dummySubmission)

        yield update_node(self.dummyNode)
        self.dummyNode['password'] = u'spam'
        self.dummyNode['old_password'] = None

    @inlineCallbacks
    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        self.setUp_dummy()
        self.responses = []
        @classmethod
        def mock_write(cls, response):
            # !!!
            # Here we are making the assumption that every time write() get's
            # called it contains *all* of the response message.
            self.responses.append(response)

        self._handler.write = mock_write
        # we make the assumption that we will always use call finish on write.
        self._handler.finish = mock_write

        try:
            yield db.createTables(create_node=True)
        except:
            pass

        yield self.fill_data()

    def tearDown(self):
        """
        Clear the actual transport.
        """
        os.unlink(_TEST_DB)

    def request(self, jbody=None, headers=None, body='', remote_ip='0.0.0.0', method='MOCK'):
        """
        :param method: HTTP method, e.g. "GET" or "POST"
        :param uri: URL to fetch
        :param headers: (dict or :class:`cyclone.httputil.HTTPHeaders` instance) HTTP headers to pass on the request
        :param body:
        :param jbody:
        :param remote_ip:
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
        return self._handler(application, request)


    def setUp_dummy(self):
        self.dummyReceiver = {
            'password': u'john',
            'name': u'john smith',
            'description': u'the first receiver',
            'tags': [],
            'languages': [u'en'],
            'notification_fields': {'mail_address': u'maker@ggay.it'},
            'can_delete_submission': True,
            'can_postpone_expiration': True,
            'can_configure_delivery': True,
            'can_configure_notification': True,
            'receiver_level': 1,
            'contexts': []
        }
        self.dummyContext = {
            'name': u'created by shooter',
            'description': u'This is the update',
            'fields': [{u'hint': u'autovelox',
                        u'label': u'city',
                        u'name': u'city',
                        u'presentation_order': 1,
                        u'required': True,
                        u'type': u'text',
                        u'value': u"Yadda I'm default with apostrophe"},
                       {u'hint': u'name of the sun',
                        u'label': u'Sun',
                        u'name': u'Sun',
                        u'presentation_order': 2,
                        u'required': True,
                        u'type': u'checkbox',
                        u'value': u"I'm the sun, I've not name"},
                       {u'hint': u'put the number ',
                        u'label': u'penality details',
                        u'name': u'dict2',
                        u'presentation_order': 3,
                        u'required': True,
                        u'type': u'text',
                        u'value': u'666 the default value'},
                       {u'hint': u'details:',
                        u'label': u'how do you know that ?',
                        u'name': u'dict3',
                        u'presentation_order': 4,
                        u'required': False,
                        u'type': u'textarea',
                        u'value': u'buh ?'}],
            'selectable_receiver': False,
            'tip_max_access': 10,
            'tip_timetolive': 2,
            'file_max_download' :1,
            'escalation_threshold': 1,
            'receivers': [],
            'languages': []
        }
        self.dummySubmission = {
            'context_gus': '',
            'wb_fields': {"city":"Milan","Sun":"warm","dict2":"happy","dict3":"blah"},
            'receivers': [],
            'files': [],
            'finalize': True,
        }
        self.dummyNode = {
                'name':  u"Please, set me: name/title",
                'description':  u"Please, set me: description",
                'hidden_service':  u"Please, set me: hidden service",
                'public_site':  u"Please, set me: public site",
                'email':  u"email@dumnmy.net",
                'stats_update_time':  2, # hours,
                'languages':  [{ "code" : "it" , "name": "Italiano"},
                               { "code" : "en" , "name" : "English" }],
                'notification_settings': {},
                'password': u'spam',
                'old_password': None,
        }

#         store = settings.get_store()
#         model = model()
#         for key, value in stuff.iteritems()
#             setattr(model, key, value)
#         store.add(model)



