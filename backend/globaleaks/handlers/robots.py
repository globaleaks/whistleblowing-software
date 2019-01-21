# -*- coding: utf-8 -*-
#
# Implementation of robots.txt resource
from six import binary_type

from globaleaks.handlers.base import BaseHandler
from globaleaks.state import State


class RobotstxtHandler(BaseHandler):
    check_roles = '*'

    def get(self):
        """
        Get the robots.txt
        """
        self.request.setHeader(b'Content-Type', b'text/plain')

        if (self.request.tid != 1 and State.tenant_cache[1].enable_signup) or \
           (not State.tenant_cache[self.request.tid].allow_indexing):
            return "User-agent: *\nDisallow: /"

        hostname = State.tenant_cache[self.request.tid].hostname
        if isinstance(hostname, binary_type):
            hostname = hostname.decode('utf-8')

        data = "User-agent: *\n"
        data += "Allow: /\n"
        data += "Sitemap: https://%s/sitemap.xml" % hostname

        return data
