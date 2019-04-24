# -*- coding: utf-8 -*-
import base64
import os

from sqlalchemy.sql.expression import func

from globaleaks.models import Config, SubmissionStatus, User


def db_fix_salt(session):
    items = session.query(Config).filter(Config.var_name == u'receipt_salt')
    for item in items:
        if len(item.value) != 24:
            item.value = base64.b64encode(os.urandom(16)).decode()


def db_fix_statuses(session):
    items = session.query(SubmissionStatus).filter(SubmissionStatus.system_usage == u'open')
    for item in items:
        item.system_usage = u'opened'
        item.label = {'en': u'Opened'}


def db_fix_users(session):
    items = session.query(User).filter(func.length(User.password) == 47)
    for item in items:
        if(item.password[0] == 'b' and item.password[1] == '\'' and item.password[len(item.password) - 1] == '\''):
            item.password = item.password[2: -1]


def db_fix(session):
    db_fix_salt(session)
    db_fix_statuses(session)
    db_fix_users(session)
