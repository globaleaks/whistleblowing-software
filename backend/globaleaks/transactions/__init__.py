# -*- coding: utf-8
"""
ORM Transactions definitions.
"""
from globaleaks import models


def db_schedule_email(session, tid, address, subject, body):
    return models.db_add(session, models.Mail,
                               {
                                   'address': address,
                                   'subject': subject,
                                   'body': body,
                                   'tid': tid,
                               })
