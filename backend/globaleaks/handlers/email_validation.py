# -*- coding: utf-8 -*-
#
# Validates the token for email changes

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import user_serialize_user
from globaleaks.orm import transact
from globaleaks.utils.security import generateRandomKey

def generate_email_change_token(session, user, new_email):
    validation_token = generateRandomKey(32)

    validation_obj = models.EmailValidations()
    validation_obj.user_id = user.id
    validation_obj.new_email = new_email
    validation_obj.validation_token = validation_token
    session.merge(validation_obj)
    session.flush()

    return validation_token

@transact
def get_email_change_token(session, validation_token):
    return db_get_email_change_token(session, validation_token)

@transact
def delete_email_change_token(session, validation_token):
    return db_delete_email_change_token(session, validation_token)

def db_get_email_change_token(session, validation_token):
    token = session.query(models.EmailValidations).filter(
        models.EmailValidations.validation_token == validation_token
    ).first()

    return token

def db_delete_email_change_token(session, validation_token):
    session.query(models.EmailValidations).filter(
        models.EmailValidations.validation_token == validation_token
    ).delete()
    session.flush()

@transact
def change_user_email(session, user_id, email):
    from globaleaks.handlers.admin.user import get_user

    user = get_user
    print(user)
    user.mail_address = email
    session.flush()

class EmailValidation(BaseHandler):
    check_roles = '*'

    @inlineCallbacks
    def get(self, validation_token):
        token = yield get_email_change_token(validation_token)
        print(token.user_id)
        if token is not None:
            yield change_user_email(token.user_id, token.new_email)
            #yield db_delete_email_change_token(validation_token)
            return self.redirect("/#/email/validation/success")
        else:
            return self.redirect("/#/email/validation/failure")

