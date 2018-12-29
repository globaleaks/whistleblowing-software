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
