# -*- coding: utf-8 -*-
#
# Implementation of sitemap resource
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks.state import State


class SitemapHandler(BaseHandler):
    """
    Handler responsible of serving the sitemap.xml resource
    """
    check_roles = 'any'

    def get(self):
        """
        Get the sitemap.xml
        """
        if not State.tenants[self.request.tid].cache.allow_indexing:
            raise errors.ResourceNotFound

        self.request.setHeader(b'Content-Type', b'text/xml')

        data = "<?xml version='1.0' encoding='UTF-8' ?>\n" + \
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n"

        if State.tenants[self.request.tid].cache.hostname:
            site = 'https://' + State.tenants[self.request.tid].cache.hostname

            data += "  <url>\n" + \
                    "    <loc>" + site + "/#/</loc>\n" + \
                    "    <changefreq>weekly</changefreq>\n" + \
                    "    <priority>1.00</priority>\n"

            for lang in sorted(State.tenants[self.request.tid].cache.languages_enabled):
                if lang != State.tenants[self.request.tid].cache.default_language:
                    hreflang = lang.lower().replace('_', '-')
                    data += "    <xhtml:link rel='alternate' hreflang='" + hreflang + "' href='" + site + "/#/?lang=" + lang + "' />\n"

            data += "  </url>\n"

        data += "</urlset>"

        return data
