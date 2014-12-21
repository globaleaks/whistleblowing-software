# -*- coding: UTF-8
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
import datetime

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.models import Receiver
from globaleaks.settings import GLSetting, transact
from globaleaks.security import GLBGPG

__all__ = ['PGPCheckSchedule']

class PGPCheckSchedule(GLJob):

    @transact
    def pgp_validation_check(self, store):

        rcvrs = store.find(Receiver)

        for rcvr in rcvrs:

            fake_receiver_dict = {'username': rcvr.user.username}

            gnob = GLBGPG(fake_receiver_dict)

            if rcvr.gpg_key_armor and gnob.validate_key(rcvr.gpg_key_armor):
                rcvr.gpg_key_info = gnob.keyinfo
                rcvr.gpg_key_fingerprint = gnob.fingerprint
                rcvr.gpg_key_status = u'Enabled'
                rcvr.gpg_enable_notification = True
            else:
                rcvr.gpg_key_info = None
                rcvr.gpg_key_fingerprint = None
                rcvr.gpg_key_status = u'Disabled'
                rcvr.gpg_key_armor = None
                rcvr.gpg_enable_notification = False

            gnob.destroy_environment()


    @inlineCallbacks
    def operation(self):
        yield self.pgp_validation_check()


untranslated_template ="""
This is an untranslated message from a GlobaLeaks node.
The PGP/GPG key configured by you: %s

Please extend their validity and update online, or upload a new
key.

When the key expire, if you've sets encrypted notification, they 
would not be send anymore at all.
"""

"""
     @transact
     def check_expiration_date(self, store):

         all_rcvs = store.find(Receiver)

         keylist = []
         keytrack = {}

         for sr in all_rcvs:
             if sr.gpg_key_status == Receiver._gpg_types[1]: # Enabled
                 keylist.append(sr.gpg_key_armor)

                 if keytrack.has_key(sr.gpg_key_fingerprint):
                     log.err("[!?] Duplicated key fingerprint between %s and %s" %
                             (sr.user.username, keytrack[sr.gpg_key_fingerprint]))

                 keytrack.update({sr.gpg_key_fingerprint : sr.user.username })

         if not keytrack:
             log.debug("PGP/GPG key expiration check: no keys configured in this node")
             return dict({}), dict({}), dict({})

         dates = get_expirations(keylist)

         today_dt = datetime.date.today()
         lowurgency = datetime.timedelta(weeks=2)
         highurgency = datetime.timedelta(days=3)

         # the return values
         expiring_keys_3d = {}
         expiring_keys_2w = {}
         expired_keys = {}

         for keyid, sincepoch in dates.iteritems():

             expiration_dt = datetime.datetime.utcfromtimestamp(int(sincepoch)).date()

             # simply, all the keys here are expired
             if expiration_dt < today_dt:
                 continue

             key_timetolife = (expiration_dt - today_dt)

             if key_timetolife < highurgency:

                 expiring_keys_3d.update({ keytrack[keyid]: sincepoch})
             elif key_timetolife < lowurgency:
                 expiring_keys_2w.update({ keytrack[keyid]: sincepoch})
             else:
                 expired_keys.update({ keytrack[keyid]: sincepoch })

         return expiring_keys_2w, expiring_keys_3d, expired_keys

    @inlineCallbacks
    def pgp_expire_check(self):

        try:
            (two_weeks, three_days, gone) = yield self.check_expiration_date()

            messages = dict({})

            for username, sincepoch in two_weeks.iteritems():
                messages.update({ username : untranslated_template % "expire in two weeks" })

            for username, sincepoch in three_days.iteritems():
                messages.update({ username : untranslated_template % "expire in three days" })

            for username, sincepoch in gone.iteritems():
                messages.update({ username : untranslated_template % "it's already expired" })

            for recipient, message in messages.iteritems():

                mail_building = ["Date: %s" % rfc822_date(),
                                 "From: \"%s\" <%s>" %
                                 ( GLSetting.memory_copy.notif_source_name,
                                   GLSetting.memory_copy.notif_source_email ),
                                 "To: %s" % recipient,
                                 "Subject: Your PGP key expiration date is coming",
                                 "Content-Type: text/plain; charset=ISO-8859-1",
                                 "Content-Transfer-Encoding: 8bit", None,
                                 message]

                mail_content = collapse_mail_content(mail_building)

                if not mail_content:
                    log.err("Unable to format (and then notify!) PGP key incoming expiration for %s" % recipient)
                    log.debug(mail_building)
                    return

                sendmail(GLSetting.memory_copy.notif_username,
                         GLSetting.memory_copy.notif_password,
                         GLSetting.memory_copy.notif_username,
                         [ recipient ],
                         mail_content,
                         GLSetting.memory_copy.notif_server,
                         GLSetting.memory_copy.notif_port,
                         GLSetting.memory_copy.notif_security)

        except Exception as excep:
            log.err("Error in PGP key expiration check: %s (failure ignored)" % excep)
            return
"""

