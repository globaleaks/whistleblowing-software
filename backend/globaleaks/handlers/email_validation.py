# -*- coding: utf-8 -*-
#
# Validates the token for email changes

from globaleaks.handlers.base import BaseHandler

class EmailValidation(BaseHandler):
    def get(self, validation_token):
        return "Test " + validation_token

