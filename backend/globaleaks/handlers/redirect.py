# -*- coding: utf-8 -*-
#
# Handlers implementing special redirects
from globaleaks.handlers.base import BaseHandler


url_map = {
    '/admin': '/#/admin',
    '/login': '/#/login',
    '/submission': '/#/submission'
}


class SpecialRedirectHandler(BaseHandler):
    """
    This handler implement the platform url shortener
    """
    check_roles = '*'

    def get(self, path):
        self.redirect(url_map[path])
