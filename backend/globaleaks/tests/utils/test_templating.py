# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import admin
from globaleaks.plugins.base import Event
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
    "admin_anomaly_mail_template":
        [generic_keyword_list, alarm_keyword_list],

    "file_mail_title":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "file_template":
        [generic_keyword_list, tip_keyword_list, file_keyword_list],

    "comment_mail_title":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "comment_template":
        [generic_keyword_list, tip_keyword_list, comment_keyword_list],

    "message_mail_title":
        [generic_keyword_list, tip_keyword_list],

    "message_template":
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
supported_event_types = {
  u'tip': 'Tip',
  u'file': 'File',
  u'comment': 'Comment',
  u'message': 'Message',
  u'zip_collection': 'Collection',
  u'ping_mail': 'Tip',
  u'admin_pgp_expiration_alert': '',
  u'pgp_expiration_alert': ''
}

class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    def _fill_event_dict(self, event_type, event_trigger):
        """
        A notification is based on the Node, Context and Receiver values,
        that has to be taken from the database.
        """
        self.subevent = {}

        # this is requested in the file cases
        if event_type == 'ping_mail':
            self.subevent = {'counter': 42}
        elif event_type == 'admin_pgp_expiration_alert':
            self.subevent = {'expired_or_expiring': [self.receiver_dict]}
        else:
            self.subevent['name'] = ' foo '
            self.subevent['size'] = ' 123 '
            self.subevent['content_type'] = ' application/javascript '
            self.subevent['creation_date'] = self.context_dict['creation_date']
            self.subevent['type'] = ' sorry maker '

        self.event = Event(type=event_type,
                           trigger=event_trigger,
                           node_info=self.node_dict,
                           receiver_info=self.receiver_dict,
                           context_info=self.context_dict,
                           steps_info=self.steps_dict,
                           tip_info=self.rtip_dict,
                           subevent_info=self.subevent,
                           do_mail=False)

    @inlineCallbacks
    def test_keywords_conversion(self):
        yield self.perform_full_submission_actions()

        self.receiver_dict = yield admin.get_receiver(self.dummyReceiver_1['id'], 'en')
        self.context_dict = yield admin.get_context(self.dummyContext['id'], 'en')
        self.steps_dict = yield admin.get_context_steps(self.dummyContext['id'], 'en')
        self.notif_dict = yield admin.notification.get_notification('en')
        self.node_dict = yield admin.admin_serialize_node('en')
        self.rtip_dict = self.dummyRTips[0]['itip']

        self.templates = {}
        for t, keywords_list in templates_desc.iteritems():

            self.templates[t] = ""

            for kwl in keywords_list:
                for keyword in kwl:
                    self.templates[t] += " " + keyword + " / "

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

            self._fill_event_dict(event_type, event_trigger)

            # with the event, we can finally call the template filler
            gentext = Templating().format_template(template, self.event)

            if template_name != 'ping_mail_template' and template_name != 'ping_mail_title':
                self.assertSubstring(self.context_dict['name'], gentext)
                self.assertSubstring(self.node_dict['public_site'], gentext)
                self.assertSubstring(self.node_dict['hidden_service'], gentext)
