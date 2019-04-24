# -*- coding: utf-8 -*-
import base64
import os

from globaleaks.models import Config, SubmissionStatus


def db_fix_salt(session):
    items = session.query(Config).filter(Config.var_name == u'receipt_salt')
    for item in items:
        try:
            if len(base64.b64decode(item.value)) != 16:
                item.value = base64.b64encode(os.urandom(16)).decode()
        except:
            item.value = base64.b64encode(os.urandom(16)).decode()


def db_fix_statuses(session):
    items = session.query(SubmissionStatus).filter(SubmissionStatus.system_usage == u'open')
    for item in items:
        item.system_usage = u'opened'
        item.label = {'en': u'Opened'}


def db_fix(session):
    db_fix_salt(session)
    db_fix_statuses(session)
