# -*- encoding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.tests.helpers import TestWithDB, MockDict
from globaleaks.handlers import admin, submission
from globaleaks.jobs import delivery_sched
from globaleaks.plugins.base import Event
from globaleaks.settings import transact_ro
from globaleaks.models import Node, InternalTip, ReceiverTip
from globaleaks.jobs.notification_sched import serialize_receivertip
from globaleaks.utils.templating import Templating


class notifTemplateTest(TestWithDB):

    templates_list = [
        'default_ETNT.txt',
        'default_PTNT.txt',
        'default_ECNT.txt',
        'default_PCNT.txt',
        'default_EMNT.txt',
        'default_PMNT.txt',
        'default_EFNT.txt',
        'default_PFNT.txt',
        'default_ZCT.txt'
    ]

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
        '%TipNum%',
    ]

    protected_keyword_list = [
        '%TipFields%'
    ]

    comment_keyword_list = [
        '%CommentSource%',
    ]

    file_keyword_list = [
        '%FileName%',
        '%FileType%',
        '%FileSize%',
    ]

    templates = {}

    @transact_ro
    def get_a_fucking_random_submission(self, store):

        aits = store.find(InternalTip)
        if not aits.count():
            # this cannot happen, but ...
            raise Exception("in our Eternal Mangekyō Sharingan, not InternalTip are avail")

        rits = store.find(ReceiverTip)
        if not rits.count():
            raise Exception("in our Eternal Mangekyō Sharingan, not ReceiverTip are avail")

        # just because 
        # storm.exceptions.UnorderedError: Can't use first() on unordered result set
        rits.order_by(Desc(ReceiverTip.id))
        return serialize_receivertip(rits.first())

    @inlineCallbacks
    def _fill_event(self, type, trigger, trigger_id):
        """
        Here I'm testing only encrypted_tip because trigger a bigger
        amount of %KeyWords%
        """
        if type == u'encrypted_tip' and trigger == 'Tip':

            receiver_dict = yield admin.get_receiver(self.createdReceiver['id'])
            context_dict = yield admin.get_context(self.createdContext['id'])
            notif_dict = yield admin.get_notification()

            try:
                yield admin.import_memory_variables()
                node_dict = yield admin.get_node()
            except Exception as exxx:
                print "Some random error with DB", exxx.__repr__()
                raise exxx

            tip_dict = yield self.get_a_fucking_random_submission()

            self.event = Event(
                type = u'encrypted_tip',
                trigger = 'Tip',
                notification_settings = notif_dict,
                node_info = node_dict,
                receiver_info = receiver_dict,
                context_info = context_dict,
                plugin = None,
                trigger_info = tip_dict,
                trigger_parent = None
            )

        elif (type == u'encrypted_file' or type == u'plaintext_comment') and trigger == 'File':
            raise AssertionError("Not yet managed Mock files")
        elif (type == u'encrypted_comment' or type == u'plaintext_comment') and trigger == 'Comment':
            raise AssertionError("Not yet managed Mock comments")
        elif (type == u'encrypted_message' or type == u'plaintext_message') and trigger == 'Message':
            raise AssertionError("Not yet managed Mock messages")
        else:
            raise AssertionError("Invalid combo: %s ~ %s" % (type, trigger))


    def _load_defaults(self):
        # CWD is on _trial_temp

        tps_path = 'globaleaks/db/'

        for t in self.templates_list:
            tp_path = os.path.join(os.getcwd(), '..', tps_path, t)

            # we simply check for file opening while translation
            # related things happen at db level
            with open(tp_path) as f:
                self.templates[t] = { "en" : f.read() }
                self.assertGreater(self.templates[t]['en'], 0)

    @inlineCallbacks
    def test_keywords_conversion(self):

        ### INITIALIZE BLOCK
        self.mockContext = MockDict().dummyContext
        self.mockReceiver = MockDict().dummyReceiver
        self.mockNode = MockDict().dummyNode

        try:
            self.createdContext = yield admin.create_context(self.mockContext)
            self.assertTrue(self.createdContext.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.mockReceiver['contexts'] = [ self.createdContext['id'] ]

            self.createdReceiver = yield admin.create_receiver(self.mockReceiver)
            self.assertTrue(self.createdReceiver.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.createdNode = yield admin.update_node(self.mockNode)
            self.assertTrue(self.createdNode.has_key('version'))
        except Exception as excep:
            raise excep
        ### END OF THE INITIALIZE BLOCK

        self.templates = {}
        for t in self.templates_list:
            self.templates[t] = { 'en': u"" }

            for k in notifTemplateTest.generic_keyword_list:
                self.templates[t]['en'] += " " + k

        for k in notifTemplateTest.tip_keyword_list:
            self.templates['default_ETNT.txt']['en'] += " " + k
            self.templates['default_PTNT.txt']['en'] += " " + k

        for k in notifTemplateTest.protected_keyword_list:
            self.templates['default_ETNT.txt']['en'] += " " + k

        for k in notifTemplateTest.comment_keyword_list:
            self.templates['default_ECNT.txt']['en'] += " " + k
            self.templates['default_PCNT.txt']['en'] += " " + k

        for k in notifTemplateTest.file_keyword_list:
            self.templates['default_EFNT.txt']['en'] += " " + k
            self.templates['default_PFNT.txt']['en'] += " " + k

        # THE REAL CONVERSION TEST START HERE:
        self.mockSubmission = MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_id'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['receiver_id'] ]
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, finalize=True)

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        try:
            yield self._fill_event(u'encrypted_tip', 'Tip', created_rtip[0])
        except Exception as excep:
            print excep; raise excep

        # with the event, we can finally call the template filler
        gentext = Templating().format_template(self.templates['default_ETNT.txt']['en'], self.event)

        self.assertSubstring(self.createdContext['name'], gentext)
        self.assertSubstring(created_rtip[0], gentext)
        self.assertSubstring(self.createdNode['public_site'], gentext)
        self.assertSubstring(self.createdNode['hidden_service'], gentext)

        ## HERE ARE ADDED SOME CHECK
        self.assertSubstring("=================", gentext)

        # http://witchwind.wordpress.com/2013/12/15/piv-is-always-rape-ok/
        # wtf has the internet in those days ? bwahahaah
        tip_num_test = Templating().format_template("%TipNum%", self.event)
        new_id = self.event.trigger_info['id'].replace('1', '2')
        new_id.replace('3', '4')
        self.event.trigger_info['id'] = new_id.replace('5', '6')
        different_num = Templating().format_template("%TipNum%", self.event)
        self.assertNotEqual(tip_num_test, different_num)


    @inlineCallbacks
    def test_default_template_keywords(self):

        self._load_defaults()

        ### INITIALIZE BLOCK
        self.mockContext = MockDict().dummyContext
        self.mockReceiver = MockDict().dummyReceiver
        self.mockNode = MockDict().dummyNode

        try:
            self.createdContext = yield admin.create_context(self.mockContext)
            self.assertTrue(self.createdContext.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.mockReceiver['contexts'] = [ self.createdContext['id'] ]

            self.createdReceiver = yield admin.create_receiver(self.mockReceiver)
            self.assertTrue(self.createdReceiver.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.createdNode = yield admin.update_node(self.mockNode)
            self.assertTrue(self.createdNode.has_key('version'))
        except Exception as excep:
            raise excep
        ### END OF THE INITIALIZE BLOCK

        # THE REAL CONVERSION TEST START HERE:
        self.mockSubmission = MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_id'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['id'] ]
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, finalize=True)

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        try:
            yield self._fill_event(u'encrypted_tip', 'Tip', created_rtip[0])
        except Exception as excep:
            print excep; raise excep

        # with the event, we can finally call the template filler
        gentext = Templating().format_template(self.templates['default_ETNT.txt'], self.event)

        self.assertSubstring(self.createdContext['name'], gentext)
        self.assertSubstring(created_rtip[0], gentext)
        self.assertSubstring(self.createdNode['public_site'], gentext)


    @inlineCallbacks
    def test_tor2web_absence(self):
        """
        This test checks:
        https://github.com/globaleaks/GlobaLeaks/issues/268
        """

        ### INITIALIZE BLOCK
        self.mockContext = MockDict().dummyContext
        self.mockReceiver = MockDict().dummyReceiver
        self.mockNode = MockDict().dummyNode

        try:
            self.createdContext = yield admin.create_context(self.mockContext)
            self.assertTrue(self.createdContext.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.mockReceiver['contexts'] = [ self.createdContext['id'] ]

            self.createdReceiver = yield admin.create_receiver(self.mockReceiver)
            self.assertTrue(self.createdReceiver.has_key('id'))
        except Exception as excep:
            raise excep

        try:
            self.createdNode = yield admin.update_node(self.mockNode)
            self.assertTrue(self.createdNode.has_key('version'))
        except Exception as excep:
            raise excep
        ### END OF THE INITIALIZE BLOCK

        # be sure of Tor2Web capability
        for attrname in Node.localized_strings:
            self.mockNode[attrname] = self.mockNode[attrname]['en']
        self.createdNode = yield admin.update_node(self.mockNode)
        yield admin.import_memory_variables()

        self._load_defaults()

        self.mockSubmission = MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_id'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['id'] ]
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, finalize=True)

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        yield self._fill_event(u'encrypted_tip', 'Tip', created_rtip[0])

        # with the event, we can finally call the format checks
        gentext = Templating().format_template(self.templates['default_ETNT.txt'], self.event)

        self.assertSubstring(self.createdContext['name'], gentext)
        self.assertSubstring(created_rtip[0], gentext)
        self.assertNotSubstring("%TipT2WURL%", gentext)
