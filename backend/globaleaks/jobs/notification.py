# -*- coding: utf-8 -*-
# Implement the notification of new submissions
import copy

import itertools

from datetime import timedelta

from sqlalchemy import and_, or_
from twisted.internet import defer

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.rtip import serialize_rtip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import db_del, transact, tw
from globaleaks.utils.log import log
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, deferred_sleep


def gen_cache_key(*args):
    return '-'.join(['{}'.format(arg) for arg in args])


class MailGenerator(object):
    def __init__(self, state):
        self.state = state
        self.cache = {}

    def serialize_config(self, session, key, tid, language):
        cache_key = gen_cache_key(key, tid, language)
        cache_obj = None

        if cache_key not in self.cache:
            if key == 'node':
                cache_obj = db_admin_serialize_node(session, tid, language)
            elif key == 'notification':
                cache_obj = db_get_notification(session, tid, language)

            self.cache[cache_key] = cache_obj

        return self.cache[cache_key]

    def process_mail_creation(self, session, tid, data):
        user_id = data['user']['id']
        language = data['user']['language']

        # Do not spool emails if the receiver has disabled notifications
        if not data['user']['notification'] or ('tip' in data and not data['tip']['enable_notifications']):
            log.debug("Discarding emails for %s due to receiver's preference.", user_id)
            return

        data['node'] = self.serialize_config(session, 'node', tid, language)

        if data['node']['mode'] == 'default':
            data['notification'] = self.serialize_config(session, 'notification', tid, language)
        else:
            data['notification'] = self.serialize_config(session, 'notification', 1, language)

        subject, body = Templating().get_mail_subject_and_body(data)

        # If the receiver has encryption enabled encrypt the mail body
        if data['user']['pgp_key_public']:
            pgpctx = PGPContext(self.state.settings.tmp_path)
            fingerprint = pgpctx.load_key(data['user']['pgp_key_public'])['fingerprint']
            body = pgpctx.encrypt_message(fingerprint, body)

        session.add(models.Mail({
            'address': data['user']['mail_address'],
            'subject': subject,
            'body': body,
            'tid': tid,
        }))

    @transact
    def generate(self, session):
        mailcount = 0
        now = datetime_now()
        rtips_ids = {}
        silent_tids = []

        reminder_time = self.state.tenant_cache[1].unread_reminder_time if 1 in self.state.tenant_cache else 7

        for tid, cache_item in self.state.tenant_cache.items():
            if cache_item.notification and cache_item.notification.disable_receiver_notification_emails:
                silent_tids.append(tid)

        results1 = session.query(models.User, models.ReceiverTip, models.InternalTip, models.ReceiverTip) \
                          .filter(models.User.id == models.ReceiverTip.receiver_id,
                                  models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                  models.ReceiverTip.new.is_(True)) \
                          .order_by(models.InternalTip.creation_date)

        results2 = session.query(models.User, models.ReceiverTip, models.InternalTip, models.Comment) \
                                 .filter(models.User.id == models.ReceiverTip.receiver_id,
                                         models.ReceiverTip.internaltip_id == models.Comment.internaltip_id,
                                         models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                         models.Comment.new.is_(True)) \
                                 .order_by(models.Comment.creation_date)

        results3 = session.query(models.User, models.ReceiverTip, models.InternalTip, models.Message) \
                            .filter(models.User.id == models.ReceiverTip.receiver_id,
                                    models.ReceiverTip.id == models.Message.receivertip_id,
                                    models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                    models.Message.new.is_(True)) \
                            .order_by(models.Message.creation_date)

        results4 = session.query(models.User, models.ReceiverTip, models.InternalTip, models.ReceiverFile) \
                          .filter(models.User.id == models.ReceiverTip.receiver_id,
                                    models.ReceiverTip.id == models.ReceiverFile.receivertip_id,
                                    models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                    models.InternalFile.id == models.ReceiverFile.internalfile_id,
                                    models.InternalFile.submission.is_(False),
                                    models.ReceiverFile.new.is_(True)) \
                          .order_by(models.InternalFile.creation_date)

        for user, rtip, itip, obj in itertools.chain(results1, results2, results3, results4):
            tid = user.tid

            if (rtips_ids.get(rtip.id, False) or tid in silent_tids) or \
               (isinstance(obj, models.Comment) and obj.type != 'whistleblower' and obj.author_id == user.id) or \
               (isinstance(obj, models.Message) and obj.type == 'receiver'):
                obj.new = False
                continue

            elif mailcount >= 20:
                continue

            obj.new = False

            rtips_ids[rtip.id] = True

            try:
                if isinstance(obj, models.ReceiverTip):
                    data = {'type': 'tip'}
                else:
                    data = {'type': 'tip_update'}

                data['user'] = user_serialize_user(session, user, user.language)
                data['tip'] = serialize_rtip(session, rtip, itip, user.language)

                self.process_mail_creation(session, tid, data)
            except:
                pass

            mailcount += 1

        for user in session.query(models.User).filter(and_(models.User.reminder_date < now - timedelta(reminder_time),
                                                           or_(and_(models.User.id == models.ReceiverTip.receiver_id,
                                                                    models.ReceiverTip.access_counter == 0,
                                                                    models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                                    models.InternalTip.creation_date < now - timedelta(reminder_time))),
                                                               and_(models.User.id == models.ReceiverTip.receiver_id,
                                                                    models.ReceiverTip.last_access < models.InternalTip.update_date,
                                                                    models.ReceiverTip.internaltip_id == models.InternalTip.id,

                                                                    models.InternalTip.update_date < now - timedelta(reminder_time)))).distinct():
            tid = user.tid

            if tid in silent_tids:
                continue

            elif mailcount >= 20:
                return

            user.reminder_date = now
            data = {'type': 'unread_tips'}

            try:
                data['user'] = self.serialize_obj(session, 'user', user, tid, user.language)
                self.process_mail_creation(session, tid, data)
            except:
                pass

            mailcount += 1


@transact
def get_mails_from_the_pool(session):
    """
    Fetch up to 20 email from the pool of email to be sent
    """
    ret = []

    for mail in session.query(models.Mail).order_by(models.Mail.creation_date).limit(20):
        ret.append({
            'id': mail.id,
            'address': mail.address,
            'subject': mail.subject,
            'body': mail.body,
            'tid': mail.tid
        })

    return ret


class Notification(LoopingJob):
    interval = 10
    monitor_interval = 3 * 60

    def generate_emails(self):
        return MailGenerator(self.state).generate()

    @defer.inlineCallbacks
    def spool_emails(self):
        delay = 1
        mails = yield get_mails_from_the_pool()
        for mail in mails:
            sent = yield self.state.sendmail(mail['tid'], mail['address'], mail['subject'], mail['body'])
            if sent:
                yield tw(db_del, models.Mail, models.Mail.id == mail['id'])
            else:
                delay = delay + 1 if delay < 10 else 10
            yield deferred_sleep(delay)

    @defer.inlineCallbacks
    def operation(self):
        yield self.generate_emails()
        yield self.spool_emails()
