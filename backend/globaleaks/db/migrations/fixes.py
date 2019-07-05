# -*- coding: utf-8 -*-
import base64
import os

from sqlalchemy.sql.expression import func

from globaleaks.models import Config, InternalTipData, SubmissionStatus, User


def db_fix_tip_data(session):
    # Fix for issue: https://github.com/globaleaks/GlobaLeaks/issues/2612
    # The bug is due to the fact that the data was initially saved as an array of one entry
    for data in session.query(InternalTipData).filter(InternalTipData.key == 'whistleblower_identity',
                                                      InternalTipData.encrypted == False):
        if isinstance(data.value, list):
            data.value = data.value[0]


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
    db_fix_statuses(session)
    db_fix_users(session)
    db_fix_tip_data(session)
