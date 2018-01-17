# -*- coding: utf-8
"""
ORM Transactions definitions.
"""
from globaleaks import models
from globaleaks.orm import transact


def db_schedule_email(session, tid, address, subject, body):
    return models.db_forge_obj(session, models.Mail,
                               {
                                   'address': address,
                                   'subject': subject,
                                   'body': body,
                                   'tid': tid,
                               })

@transact
def schedule_email(session, tid, address, subject, body):
    return db_schedule_email(session, tid, address, subject, body)


@transact
def schedule_email_for_all_admins(session, subject, body):
    from globaleaks.handlers.admin.user import db_get_admin_users
    for user_desc in db_get_admin_users(session, 1):
        db_schedule_email(session, 1, user_desc['mail_address'], subject, body)
