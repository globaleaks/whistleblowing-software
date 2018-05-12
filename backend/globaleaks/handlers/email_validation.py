# -*- coding: utf-8 -*-
#
# Validates the token for email changes

from datetime import datetime, timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.utils.security import generateRandomKey

@transact
def generate_email_change_token(session, user, new_email):
    return db_generate_email_change_token(session, user, new_email)


def db_generate_email_change_token(session, user_id, new_email):
    validation_token = generateRandomKey(32)

    validation_obj = models.EmailValidations()
    validation_obj.user_id = user_id
    validation_obj.new_email = new_email
    validation_obj.validation_token = validation_token
    session.merge(validation_obj)

    return validation_token


@transact
def get_email_change_token(session, validation_token):
    '''transact version of db_get_email_change_token'''
    return db_get_email_change_token(session, validation_token)


def db_get_email_change_token(session, validation_token):
    '''Retrieves an email change token for validation in the backend'''
    token = session.query(models.EmailValidations).filter(
        models.EmailValidations.validation_token == validation_token
    ).one()

    if token is not None:
        session.expunge(token)

    return token


@transact
def delete_email_change_token(session, validation_token):
    '''transact wrapper for db_delete_email_change_token'''
    return db_delete_email_change_token(session, validation_token)


def db_delete_email_change_token(session, validation_token):
    '''Deletes an email change token, done if it's expired or used successfully'''

    session.query(models.EmailValidations).filter(
        models.EmailValidations.validation_token == validation_token
    ).delete()


@transact
def change_user_email(session, user_id, email):
    '''Updates the email address in the database from the emailvalidation token'''

    user = models.db_get(session, models.User, models.User.id == user_id)
    user.mail_address = email


class EmailValidation(BaseHandler):
    check_roles = '*'

    @inlineCallbacks
    def get(self, validation_token):
        token = yield get_email_change_token(validation_token)
        if token is not None:
            # Tokens are only valid for 72 hours from their creation data
            if token.creation_date-timedelta(hours=72) > datetime.now():
                # Token is expired
                yield delete_email_change_token(validation_token)
                self.redirect("/#/email/validation/failure")
                return

            # If the token is valid, change the email and delete the token
            yield change_user_email(token.user_id, token.new_email)
            yield delete_email_change_token(validation_token)
            self.redirect("/#/email/validation/success")
        else:
            self.redirect("/#/email/validation/failure")
