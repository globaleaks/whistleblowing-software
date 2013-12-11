import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests.helpers import TestWithDB
from globaleaks.handlers import admin, submission
from globaleaks.jobs import delivery_sched
from globaleaks.plugins.base import Event
from globaleaks.plugins.notification import MailNotification
from globaleaks.tests.helpers import MockDict
from globaleaks.utils.utility import datetime_now, pretty_date_time
from globaleaks.models import Node


class notifTemplateTest(TestWithDB):

    generic_keyword_list = [
        '%NodeName%',
        '%HiddenService%',
        '%PublicSite%',
        '%ReceiverName%',
        '%ContextName%',
    ]

    tip_keyword_list = [
        '%TipTorURL%',
        '%TipT2WURL%',
    ]

    comment_keyword_list = [
        '%CommentSource%',
    ]

    file_keyword_list = [
        '%FileName%',
        '%FileType%',
        '%FileSize%',
    ]

    @inlineCallbacks
    def _initialize(self):

        self.mockContext = MockDict().dummyContext
        self.mockReceiver = MockDict().dummyReceiver
        self.mockNode = MockDict().dummyNode

        try:
            self.createdContext = yield admin.create_context(self.mockContext)
            self.assertTrue(self.createdContext.has_key('context_gus'))
        except Exception as excep:
            self.assertFalse(True)
            raise excep

        try:
            self.mockReceiver['contexts'] = [ self.createdContext['context_gus'] ]
            self.createdReceiver = yield admin.create_receiver(self.mockReceiver)
            self.assertTrue(self.createdReceiver.has_key('receiver_gus'))
        except Exception as excep:
            self.assertFalse(True)
            raise excep

        try:
            self.createdNode = yield admin.update_node(self.mockNode)
            self.assertTrue(self.createdNode.has_key('version'))
        except Exception as excep:
            self.assertFalse(True)
            raise excep


    @inlineCallbacks
    def _fill_event(self, type, trigger, trigger_id):

        if type == u'tip' and trigger == 'Tip':

            receiver_dict = yield admin.get_receiver(self.createdReceiver['receiver_gus'])
            context_dict = yield admin.get_context(self.createdContext['context_gus'])
            notif_dict = yield admin.get_notification()

            yield admin.import_memory_variables()
            node_dict = yield admin.get_node()

            self.event = Event(
                type = u'tip',
                trigger = 'Tip',
                notification_settings = notif_dict,
                node_info = node_dict,
                receiver_info = receiver_dict,
                context_info = context_dict,
                plugin = None,
                trigger_info = {
                   'id': trigger_id,
                   'creation_date': pretty_date_time(datetime_now())
                }
            )

        elif type == u'comment' and trigger == 'Comment':
            raise AssertionError("Not yet managed Mock comments")
        elif type == u'file' and trigger == 'File':
            raise AssertionError("Not yet managed Mock files")
        else:
            raise AssertionError("type and trigger maybe refactored, but you're using it bad")


    def _load_defaults(self):
        # CWD is on _trial_temp
        CNT = os.path.join(os.getcwd(), '..', 'globaleaks', 'db', 'default_CNT.txt')
        TNT = os.path.join(os.getcwd(), '..', 'globaleaks', 'db', 'default_TNT.txt')
        FNT = os.path.join(os.getcwd(), '..', 'globaleaks', 'db', 'default_FNT.txt')

        if not os.path.isfile(CNT):
            raise AssertionError("path mistake ?")

        # here is fine the localization, it's DB feeding
        with open(CNT) as f:
            self.Comment_notif_template = { "en" : f.read() }

        with open(TNT) as f:
            self.Tip_notifi_template = { "en" : f.read() }

        with open(FNT) as f:
            self.File_notifi_template = { "en" : f.read() }

        self.assertGreater(self.Comment_notif_template['en'], 0)
        self.assertGreater(self.Tip_notifi_template['en'], 0)
        self.assertGreater(self.File_notifi_template['en'], 0)



    @inlineCallbacks
    def test_keywords(self):

        yield self._initialize()
        self._load_defaults()

        self.mockSubmission = MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_gus'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['receiver_gus'] ]
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, finalize=True)

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        try:
            yield self._fill_event(u'tip', 'Tip', created_rtip[0])
        except Exception as excep:
            print excep; raise excep

        # with the event, we can finally call the template filler
        gentext = MailNotification().format_template(self.Tip_notifi_template, self.event)

        self.assertSubstring(self.createdContext['name'], gentext)
        self.assertSubstring(created_rtip[0], gentext)
        self.assertSubstring(self.createdNode['public_site'], gentext)
        self.assertSubstring(self.createdNode['hidden_service'], gentext)


    @inlineCallbacks
    def test_tor2web_absence(self):
        """
        This test checks:
        https://github.com/globaleaks/GlobaLeaks/issues/268
        """

        yield self._initialize()

        # be sure of Tor2Web capability
        self.mockNode['tor2web_tip'] = False
        for attrname in Node.localized_strings:
            self.mockNode[attrname] = self.mockNode[attrname]['en']
        self.createdNode = yield admin.update_node(self.mockNode)
        yield admin.import_memory_variables()

        self._load_defaults()

        self.mockSubmission = MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_gus'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['receiver_gus'] ]
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, finalize=True)

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        yield self._fill_event(u'tip', 'Tip', created_rtip[0])

        # with the event, we can finally call the format checks
        gentext = MailNotification().format_template(self.Tip_notifi_template, self.event)

        self.assertSubstring(self.createdContext['name'], gentext)
        self.assertSubstring(created_rtip[0], gentext)
        self.assertNotSubstring("%TipT2WURL%", gentext)
