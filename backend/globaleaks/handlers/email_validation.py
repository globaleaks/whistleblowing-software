# -*- coding: utf-8 -*-
#
# Validates the token for email changes

from datetime import datetime, timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.utils.utility import datetime_now
from globaleaks.utils.security import generateRandomKey

@transact
def validate_address_change(session, validation_token):
    '''transact version of db_validate_address_change'''
    return db_validate_address_change(session, validation_token)


def db_validate_address_change(session, validation_token):
    '''Retrieves a user given a mail change validation token'''
    user = session.query(models.User).filter(
        models.User.change_email_token == validation_token,
        models.User.change_email_date >= datetime.now() - timedelta(hours=72)
    ).one_or_none()

    if user is None:
        return False

    user.mail_address = user.change_email_address
    user.change_email_token = None
    user.change_email_address = u''
    user.change_email_date = datetime_now()

    return True


class EmailValidation(BaseHandler):
    check_roles = '*'
    redirect_url = "/#/email/validation/success"

    @inlineCallbacks
    def get(self, validation_token):
        check = yield validate_address_change(validation_token)
        if not check:
            self.redirect_url = "/#/email/validation/failure"

        self.redirect(self.redirect_url)
