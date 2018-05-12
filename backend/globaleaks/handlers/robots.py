# -*- coding: utf-8 -*-
#
# Handlerse dealing with robots/sitemap resources
from six import binary_type

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks.state import State

class RobotstxtHandler(BaseHandler):
    check_roles = '*'

    def get(self):
        """
        Get the robots.txt
        """
        self.request.setHeader('Content-Type', 'text/plain')

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


class SitemapHandler(BaseHandler):
    check_roles = '*'

    def get(self):
        """
        Get the sitemap.xml
        """
        if not State.tenant_cache[self.request.tid].allow_indexing:
            raise errors.ResourceNotFound()

        site = 'https://' + State.tenant_cache[self.request.tid].hostname

        self.request.setHeader('Content-Type', 'text/xml')

        data = "<?xml version='1.0' encoding='UTF-8' ?>\n" + \
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n"

        urls = ['/#/', '/#/submission']

        if (self.request.tid == 1 and State.tenant_cache[1].enable_signup):
            urls.append('/#/signup')

        for url in urls:
            data += "  <url>\n" + \
                    "    <loc>" + site + url + "</loc>\n" + \
                    "    <changefreq>weekly</changefreq>\n" + \
                    "    <priority>1.00</priority>\n"

            for lang in sorted(State.tenant_cache[self.request.tid].languages_enabled):
                if lang != State.tenant_cache[self.request.tid].default_language:
                    l = lang.lower()
                    l = l.replace('_', '-')
                    data += "<xhtml:link rel='alternate' hreflang='" + l + "' href='" + site + url + "?lang=" + lang + "' />\n"

            data += "  </url>\n"

        data += "</urlset>"

        return data
