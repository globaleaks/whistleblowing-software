# -*- coding: utf-8 -*-
#
# Validates the token for email changes

import globaleaks
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
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
    return models.db_get(session, models.EmailValidations, models.EmailValidations == validation_token)


class EmailValidation(BaseHandler):
    check_roles = '*'

    def get(self, validation_token):
        print(validation_token)
        try:
            token = get_email_change_token(validation_token)
            return self.redirect("/#/email/validation/success")
        except globaleaks.rest.errors.ModelNotFound:
            return self.redirect("/#/email/validation/failure")

