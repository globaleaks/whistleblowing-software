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

ping_keyword_list = [
    "%ReceiverName%",
    "%EventCount%"
]

admin_pgp_alert_keywords = [
    "%PGPKeyInfoList%"
]

pgp_alert_keywords = [
    "%PGPKeyInfo%"
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
        [generic_keyword_list, tip_keyword_list],

    "ping_mail_template":
        [generic_keyword_list, ping_keyword_list],

    "ping_mail_title":
        [generic_keyword_list, ping_keyword_list],

    "admin_pgp_expiration_alert_mail_template":
        [generic_keyword_list, admin_pgp_alert_keywords],

    "admin_pgp_expiration_alert_mail_title":
        [generic_keyword_list, admin_pgp_alert_keywords],

    "pgp_expiration_alert_mail_template":
        [generic_keyword_list, pgp_alert_keywords],

    "pgp_expiration_alert_mail_title":
        [generic_keyword_list, pgp_alert_keywords],
}

# Templating 'supported_event_type' is a method variable with a different pattern
# the whole test can be re-engineered
supported_event_types = { u'encrypted_tip': 'Tip',
                          u'plaintext_tip': 'Tip',
                          u'encrypted_file': 'File',
                          u'plaintext_file': 'File',
                          u'encrypted_comment': 'Comment',
                          u'plaintext_comment': 'Comment',
                          u'encrypted_message': 'Message',
                          u'plaintext_message': 'Message',
                          u'zip_collection': 'Collection',
                          u'ping_mail': 'Tip',
                          u'admin_pgp_expiration_alert': '',
                          u'pgp_expiration_alert': ''}

class notifTemplateTest(helpers.TestGL):
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

        self.subevent = {}

        # this is requested in the file cases
        if event_type == 'ping_mail':
            self.subevent = {'counter': 42}
        elif event_type == 'admin_pgp_expiration_alert':
            self.subevent = {'expired_or_expiring': [receiver_dict]}
        else:
            self.subevent['name'] = ' foo '
            self.subevent['size'] = ' 123 '
            self.subevent['content_type'] = ' application/javascript '
            self.subevent['creation_date'] = context_dict['creation_date']
            self.subevent['type'] = ' sorry maker '

        self.event = Event(type=event_type,
                           trigger=event_trigger,
                           node_info=node_dict,
                           receiver_info=receiver_dict,
                           context_info=context_dict,
                           steps_info=steps_dict,
                           tip_info=self.tip,
                           subevent_info=self.subevent,
                           do_mail=False)

    @inlineCallbacks
    def test_keywords_conversion(self):
        self.templates = {}
        for t, keywords_list in templates_desc.iteritems():

            self.templates[t] = ""

            for kwl in keywords_list:
                for keyword in kwl:
                    self.templates[t] += " " + keyword + " / "

        ### INITIALIZE DATABASE
        self.mockContext = helpers.MockDict().dummyContext
        self.mockReceiver = helpers.MockDict().dummyReceiverGPG
        self.mockNode = helpers.MockDict().dummyNode

        self.createdContext = yield admin.create_context(self.mockContext, 'en')
        self.assertTrue('id' in self.createdContext)

        self.mockReceiver['contexts'] = [ self.createdContext['id'] ]

        self.createdReceiver = yield admin.create_receiver(self.mockReceiver, 'en')
        self.assertTrue('id' in self.createdReceiver)

        self.createdNode = yield admin.update_node(self.mockNode, True, 'en')
        self.assertTrue('version' in self.createdNode)
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

        for template_name, template in self.templates.iteritems():
            # look for appropriate event_type, event_trigger
            event_type = u''
            event_trigger = ''
            for e_t, e_tri in supported_event_types.iteritems():
                if template_name.startswith(e_t):
                    event_type = e_t
                    event_trigger = e_tri
                    break

            if not event_type:
                # we've nothing to do not!
                continue

            yield self._fill_event_dict(event_type, event_trigger)

            # with the event, we can finally call the template filler
            gentext = Templating().format_template(template, self.event)

            if template_name != 'ping_mail_template' and template_name != 'ping_mail_title':
                self.assertSubstring(self.createdContext['name'], gentext)
                self.assertSubstring(self.createdNode['public_site'], gentext)
                self.assertSubstring(self.createdNode['hidden_service'], gentext)
