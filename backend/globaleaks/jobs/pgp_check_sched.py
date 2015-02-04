
#
#   pgp_check_sched
#   ***************
#
# Implements periodic checks in order to verify pgp key status and other consistencies:
# 
# to be implemented:
#     if keys configured by receiver are going
#     to expire in short time, if so, send a warning email to the recipient.
#
from cyclone.util import ObjectDict as OD
from twisted.internet.defer import inlineCallbacks

from datetime import timedelta

from globaleaks.handlers.admin import admin_serialize_user, \
    admin_serialize_receiver, admin_serialize_node, db_admin_serialize_node
from globaleaks.handlers.admin.notification import get_notification
from globaleaks.jobs.base import GLJob
from globaleaks.models import Receiver
from globaleaks.settings import transact, GLSetting
from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.utils.utility import datetime_now, datetime_null
from globaleaks.utils.templating import Templating


__all__ = ['PGPCheckSchedule']

class PGPCheckSchedule(GLJob):

    @transact
    def pgp_validation_check(self, store):
        node_desc = db_admin_serialize_node(store, 'en')

        expired_or_expiring = []

        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:

            if rcvr.gpg_key_armor and rcvr.gpg_key_expiration != datetime_null():
               if rcvr.gpg_key_expiration < datetime_now():
                   expired_or_expiring.append(admin_serialize_receiver(rcvr, GLSetting.memory_copy.default_language))
                   if node_desc['allow_unencrypted']:
                       # The PGP key status should be downgraded only if the node
                       # accept non PGP mails/files to be sent/stored.
                       # If the node wont accept this the pgp key status
                       # will remain enabled and mail won't be sent by regular flow.
                       rcvr.gpg_key_status = u'disabled'
               elif rcvr.gpg_key_expiration < datetime_now() - timedelta(days=15):
                   expired_or_expiring.append(admin_serialize_receiver(rcvr, GLSetting.memory_copy.default_language))

        return expired_or_expiring

    @inlineCallbacks
    def send_admin_pgp_alerts(self, node_desc, admin_desc, notification_settings, expired_or_expiring):
        fakeevent = OD()
        fakeevent.type = u'admin_pgp_expiration_alert'
        fakeevent.node_info = node_desc
        fakeevent.context_info = None
        fakeevent.steps_info = None
        fakeevent.receiver_info = None
        fakeevent.tip_info = None
        fakeevent.subevent_info = {'expired_or_expiring': expired_or_expiring}

        body = Templating().format_template(
            notification_settings['admin_pgp_alert_mail_template'], fakeevent)
        title = Templating().format_template(
            notification_settings['admin_pgp_alert_mail_title'], fakeevent)

        to_address = node_desc['email']
        message = MIME_mail_build(GLSetting.memory_copy.notif_source_name,
                                  GLSetting.memory_copy.notif_source_email,
                                  to_address,
                                  to_address,
                                  title,
                                  body)

        yield sendmail(authentication_username=GLSetting.memory_copy.notif_username,
                       authentication_password=GLSetting.memory_copy.notif_password,
                       from_address=GLSetting.memory_copy.notif_source_email,
                       to_address=to_address,
                       message_file=message,
                       smtp_host=GLSetting.memory_copy.notif_server,
                       smtp_port=GLSetting.memory_copy.notif_port,
                       security=GLSetting.memory_copy.notif_security,
                       event=None)

    @inlineCallbacks
    def send_pgp_alerts(self, node_desc, receiver_desc, notification_settings):
        fakeevent = OD()
        fakeevent.type = u'pgp_expiration_alert'
        fakeevent.node_info = node_desc
        fakeevent.context_info = None
        fakeevent.steps_info = None
        fakeevent.receiver_info = receiver_desc
        fakeevent.tip_info = None
        fakeevent.subevent_info = None

        body = Templating().format_template(
            notification_settings['pgp_alert_mail_template'], fakeevent)
        title = Templating().format_template(
            notification_settings['pgp_alert_mail_title'], fakeevent)

        to_address = receiver_desc['mail_address']
        message = MIME_mail_build(GLSetting.memory_copy.notif_source_name,
                                  GLSetting.memory_copy.notif_source_email,
                                  to_address,
                                  to_address,
                                  title,
                                  body)

        yield sendmail(authentication_username=GLSetting.memory_copy.notif_username,
                       authentication_password=GLSetting.memory_copy.notif_password,
                       from_address=GLSetting.memory_copy.notif_source_email,
                       to_address=to_address,
                       message_file=message,
                       smtp_host=GLSetting.memory_copy.notif_server,
                       smtp_port=GLSetting.memory_copy.notif_port,
                       security=GLSetting.memory_copy.notif_security,
                       event=None)

    @inlineCallbacks
    def operation(self):
        expired_or_expiring = yield self.pgp_validation_check()

        admin_user = yield admin_serialize_user('admin')

        node_desc = yield admin_serialize_node(admin_user['language'])

        notification_settings = yield get_notification(admin_user['language'])

        if expired_or_expiring:
            yield self.send_admin_pgp_alerts(node_desc, admin_user, notification_settings, expired_or_expiring)

            for receiver_desc in expired_or_expiring:
                yield self.send_pgp_alerts(node_desc, receiver_desc, notification_settings)

