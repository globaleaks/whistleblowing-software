# -*- encoding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.tests import helpers
from globaleaks.handlers import admin, submission
from globaleaks.handlers.admin.field import create_field
from globaleaks.jobs import delivery_sched
from globaleaks.plugins.base import Event
from globaleaks.settings import transact_ro
from globaleaks.models import Node, Notification, InternalTip, ReceiverTip
from globaleaks.jobs.notification_sched import serialize_receivertip
from globaleaks.utils.templating import Templating

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

alarm_keyword_list = [
    "%ActivityAlarmLevel%",
    "%ActivityDump%",
    "%DiskAlarmLevel%",
    "%DiskDump%",
]

templates_desc = {
    "admin_anomaly_template":
        [generic_keyword_list, alarm_keyword_list],

    "encrypted_comment_mail_title":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "encrypted_comment_template":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "encrypted_file_mail_title":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "encrypted_file_template":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "encrypted_message_mail_title":
        [generic_keyword_list, tip_keyword_list],

    "encrypted_message_template" :
        [generic_keyword_list, tip_keyword_list],

    "encrypted_tip_mail_template":
        [generic_keyword_list, tip_keyword_list],

    "encrypted_tip_mail_title":
        [generic_keyword_list, tip_keyword_list],

    "encrypted_tip_template":
        [generic_keyword_list, tip_keyword_list, protected_keyword_list],

    "pgp_expiration_alert":
        [generic_keyword_list],

    "pgp_expiration_notice":
        [generic_keyword_list],

    "plaintext_comment_mail_title":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "plaintext_comment_template":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "plaintext_file_mail_title":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "plaintext_file_template":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "plaintext_message_mail_title":
        [generic_keyword_list, tip_keyword_list],

    "plaintext_message_template":
        [generic_keyword_list, tip_keyword_list],

    "plaintext_tip_mail_title":
        [generic_keyword_list, tip_keyword_list],

    "plaintext_tip_template":
        [generic_keyword_list, tip_keyword_list],

    "zip_description.txt":
        [generic_keyword_list, tip_keyword_list]
}

# Templating 'supported_event_type' is a method variable with a different pattern
# the whole test can be re-engineered
supported_event_types = { u'encrypted_tip' : 'Tip',
                          u'plaintext_tip' : 'Tip',
                          u'encrypted_file' : 'File',
                          u'plaintext_file' : 'File',
                          u'encrypted_comment' : 'Comment',
                          u'plaintext_comment' : 'Comment',
                          u'encrypted_message' : 'Message',
                          u'plaintext_message' : 'Message',
                          u'zip_collection' : 'Collection'
                          }

class notifTemplateTest(helpers.TestGL):
    """
    Not yet implemented, but present in templating.py

    u'encrypted_expiring_tip' : 'Tip',
    u'plaintext_expiring_tip' : 'Tip',
    """

    @inlineCallbacks
    def _fill_event_dict(self, event_type, event_trigger):
        """
        A notification is based on the Node, Context and Receiver values,
        that has to be taken from the database.
        """
        receiver_dict = yield admin.get_receiver(self.createdReceiver['id'], 'en')
        context_dict = yield admin.get_context(self.createdContext['id'], 'en')
        steps_dict = yield admin.get_context_steps(self.createdContext['id'], 'en')
        notif_dict = yield admin.notification.get_notification('en')

        node_dict = yield admin.admin_serialize_node('en')

        # is a mock 'trigger_info' and 'trigger_parent' at the moment
        self.tip['name'] = ' foo '
        self.tip['size'] = ' 123 '
        self.tip['content_type'] = ' application/javascript '
        self.tip['creation_date'] = context_dict['creation_date']
        self.tip['type'] = ' sorry maker '
        # this is requested in the file cases

        self.event = Event(type = event_type,
                           trigger = event_trigger,
                           notification_settings = notif_dict,
                           node_info = node_dict,
                           receiver_info = receiver_dict,
                           context_info = context_dict,
                steps_info = steps_dict,
                           plugin = None,
                           trigger_info = self.tip,
                           trigger_parent = self.tip )

    @inlineCallbacks
    def _fill_event(self, event_type, trigger, trigger_id):
        """
        Here I'm testing only encrypted_tip because trigger a bigger
        amount of %KeyWords%
        """
        self.assertEqual(event_type, u'encrypted_tip')
        self.assertEqual(trigger, 'Tip')

        if event_type == u'encrypted_tip' and trigger == 'Tip':

            receiver_dict = yield admin.get_receiver(self.createdReceiver['id'], 'en')
            context_dict = yield admin.get_context(self.createdContext['id'], 'en')
            steps_dict = yield admin.get_context_steps(self.createdContext['id'], 'en')
            notif_dict = yield admin.notification.get_notification('en')

            node_dict = yield admin.admin_serialize_node('en')

            tip_dict = yield self.get_a_fucking_random_submission()

            self.event = Event(
                type = u'encrypted_tip',
                trigger = 'Tip',
                notification_settings = notif_dict,
                node_info = node_dict,
                receiver_info = receiver_dict,
                context_info = context_dict,
                steps_info = steps_dict,
                plugin = None,
                trigger_info = tip_dict,
                trigger_parent = None
            )

    @transact_ro
    def _load_defaults(self, store):
        notif = store.find(Notification).one()
        for t, _ in self.templates_desc:
            self.templates[t] = getattr(notif, t)['en']

    @inlineCallbacks
    def test_keywords_conversion(self):
        self.templates = {}
        for t, keywords_list in templates_desc.iteritems():

            self.templates[t] = ""

            for kwl in keywords_list:
                for keyword in kwl:
                    self.templates[t] += " " + keyword + " / "

        ### INITIALIZE DATABASE
        self.mockContext =helpers.MockDict().dummyContext
        self.mockReceiver = helpers.MockDict().dummyReceiver
        self.mockNode = helpers.MockDict().dummyNode

        self.createdContext = yield admin.create_context(self.mockContext, 'en')
        self.assertTrue(self.createdContext.has_key('id'))

        self.mockReceiver['contexts'] = [ self.createdContext['id'] ]

        self.createdReceiver = yield admin.create_receiver(self.mockReceiver, 'en')
        self.assertTrue(self.createdReceiver.has_key('id'))

        self.createdNode = yield admin.update_node(self.mockNode, True, 'en')
        self.assertTrue(self.createdNode.has_key('version'))
        ### END OF THE INITIALIZE BLOCK

        # THE REAL CONVERSION TEST START HERE:
        self.mockSubmission = helpers.MockDict().dummySubmission
        self.mockSubmission['finalize'] = True
        self.mockSubmission['context_id'] = self.createdReceiver['contexts'][0]
        self.mockSubmission['receivers'] = [ self.createdReceiver['id'] ]
        self.mockSubmission['wb_fields'] = helpers.fill_random_fields(self.createdContext)
        self.createdSubmission = yield submission.create_submission(self.mockSubmission, True, 'en')

        created_rtip = yield delivery_sched.tip_creation()
        self.assertEqual(len(created_rtip), 1)

        # some doubt in the next two lines: is just to have a mock tip
        self.tip = dict(self.mockSubmission)
        self.tip['id'] = created_rtip[0]

        for fname, template in self.templates.iteritems():

            # look for appropriate event_type, event_trigger
            event_type = u''
            event_trigger = ''
            for e_t, e_tri in supported_event_types.iteritems():
                if fname.startswith(e_t):
                    event_type = e_t
                    event_trigger = e_tri
                    break

            if not event_type:
                # we've nothing to do not!
                break

            yield self._fill_event_dict(event_type, event_trigger)

            # with the event, we can finally call the template filler
            gentext = Templating().format_template(template, self.event)

            self.assertSubstring(self.createdContext['name'], gentext)
            self.assertSubstring(self.createdNode['public_site'], gentext)
            self.assertSubstring(self.createdNode['hidden_service'], gentext)
