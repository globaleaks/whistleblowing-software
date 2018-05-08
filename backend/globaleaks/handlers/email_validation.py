# -*- coding: utf-8 -*-
#
# Validates the token for email changes

from globaleaks.handlers.base import BaseHandler

class EmailValidation(BaseHandler):
    check_roles = '*'

    def get(self, validation_token):
        return self.redirect("/#/email/validation/success")