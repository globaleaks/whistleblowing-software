# -*- coding: UTF-8
# public
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from globaleaks.handlers.base import BaseHandler
from globaleaks.settings import GLSettings


class RobotstxtHandler(BaseHandler):
    @BaseHandler.transport_security_check("unauth")
    @BaseHandler.unauthenticated
    def get(self):
        """
        Get the robots.txt
        """
        self.set_header('Content-Type', 'text/plain')

        self.write("User-agent: *\n")

        if GLSettings.memory_copy.allow_indexing:
            self.write("Allow: /\n")
            self.write("Sitemap: %s/sitemap.xml" % GLSettings.memory_copy.public_site)
        else:
            self.write("Disallow: /")


class SitemapHandler(BaseHandler):
    @BaseHandler.transport_security_check("unauth")
    @BaseHandler.unauthenticated
    def get(self):
        """
        Get the sitemap.xml
        """
        if not GLSettings.memory_copy.allow_indexing:
            self.set_status(404)
            return

        self.set_header('Content-Type', 'text/xml')

        self.write("<?xml version='1.0' encoding='UTF-8' ?>\n" +
                   "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n")

        for url in ['/#/', '/#/submission']:
            self.write("  <url>\n" +
                       "    <loc>" + GLSettings.memory_copy.public_site + url + "</loc>\n" +
                       "    <changefreq>weekly</changefreq>\n" +
                       "    <priority>1.00</priority>\n")

            for lang in sorted(GLSettings.memory_copy.languages_enabled):
                if lang != GLSettings.memory_copy.default_language:
                    l = lang.lower()
                    l = l.replace('_', '-')
                    self.write("    <xhtml:link rel='alternate' hreflang='" + l + "' href='" + GLSettings.memory_copy.public_site + "/#/?lang=" + lang + "' />\n")

            self.write("  </url>\n")

        self.write("</urlset>")
