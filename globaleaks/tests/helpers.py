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


from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks import models
from globaleaks.utils import idops, gltime
from globaleaks import settings
from globaleaks import db

_TEST_DB = 'test.db'
settings.db_file = 'sqlite:///' + _TEST_DB
settings.store = 'test_store'
settings.config = settings.Config()

import storm

class TestHandler(unittest.TestCase):
    """
    :attr _handler: handler class to be tested
    """
    _handler = None

    @transact
    def fill_data(self):
        receiver = models.receiver.Receiver(self.store).new(dummyReceiver)
        dummyReceiver['username'] = receiver['username']

        dummyContext['receivers'] = receiver['receiver_gus']
        context = models.context.Context(self.store).new(dummyContext)

        dummySubmission['context_gus'] = context['context_gus']
        submission = models.submission.Submission(self.store).new(dummySubmission)

        dummyNode['context_gus'] = context['context_gus']
        models.node.Node(self.store).new(dummyNode)

        node = self.store.find(models.node.Node).one()
        node.password = u'spam'

        internal_tip = models.internaltip.InternalTip(self.store).new(dummySubmission)
        self.dummyWhistleblowerTip = models.externaltip.WhistleblowerTip(self.store).new(internal_tip)



    @inlineCallbacks
    def setUp(self):
        """
        override default handlers' get_store with a mock store used for testing/
        """
        self.responses = []
        @classmethod
        def mock_write(cls, response):
            # !!!
            # Here we are making the assumption that every time write() get's
            # called it contains *all* of the response message.
            self.responses.append(response)

        # override handle's get_store and transactor
        self._handler.write = mock_write

        try:
            yield transact.run(db.createTables(create_node=False))
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

#         store = settings.get_store()
#         model = model()
#         for key, value in stuff.iteritems()
#             setattr(model, key, value)
#         store.add(model)


dummyReceiver = {
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
}
dummyContext = {
    'name': u'created by shooter',
    'description': u'This is the update',
    'fields':[{"hint": u"autovelox", "label": "city", "name": "city", "presentation_order": 1, "required": True, "type": "text", "value": "Yadda I'm default with apostrophe" },
              {"hint": u"name of the sun", "label": "Sun", "name": "Sun", "presentation_order": 2, "required": True, "type": "checkbox", "value": "I'm the sun, I've not name" },
              {"hint": u"put the number ", "label": "penality details", "name": "dict2", "presentation_order": 3, "required": True, "type": "text", "value": "666 the default value" },
              {"hint": u"details:", "label": "how do you know that ?", "name": "dict3", "presentation_order": 4, "required":
                  False, "type": "textarea", "value": "buh ?" },
    ],
    'selectable_receiver': False,
    'tip_max_access': 10,
    'tip_timetolive': 2,
    'file_max_download' :1,
    'escalation_threshold': 1,
    'receivers': []
}
dummySubmission = {
    'context_gus': '',
    'wb_fields': {"city":"Milan","Sun":"warm","dict2":"happy","dict3":"blah"},
    'receivers': [],
    'files': [],
    'finalize': True,
}
dummyNode = {
        'name':  u"Please, set me: name/title",
        'description':  u"Please, set me: description",
        'hidden_service':  u"Please, set me: hidden service",
        'public_site':  u"Please, set me: public site",
        'email':  u"email@dumnmy.net",
        'stats_update_time':  2, # hours,
        'languages':  [{ "code" : "it" , "name": "Italiano"},
                       { "code" : "en" , "name" : "English" }],
        'notification_settings': {},
}
