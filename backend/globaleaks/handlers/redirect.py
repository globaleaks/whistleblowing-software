# -*- coding: utf-8
#
# redirect
# **************
#

from twisted.internet.defer import inlineCallbacks, returnValue
from globaleaks.handlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """
    Login redirection
    """
    check_roles = '*'

    def get(self):
        """
        Redirect requests
        """

        self.redirect('/#/login')

