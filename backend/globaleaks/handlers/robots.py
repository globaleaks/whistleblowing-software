# -*- coding: utf-8
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

        data = "User-agent: *\n"

        if State.tenant_cache[1].allow_indexing:
            site = 'https://' + State.tenant_cache[1].hostname
            data += "Allow: /\n"
            data += "Sitemap: %s/sitemap.xml\n" % site
        else:
            data += "Disallow: /\n"

        data += "TenantID: %d\n" % self.request.tid
        return data


class SitemapHandler(BaseHandler):
    check_roles = '*'

    def get(self):
        """
        Get the sitemap.xml
        """
        if not State.tenant_cache[1].allow_indexing:
            raise errors.ResourceNotFound()

        site = 'https://' + State.tenant_cache[1].hostname

        self.request.setHeader('Content-Type', 'text/xml')

        data = "<?xml version='1.0' encoding='UTF-8' ?>\n" + \
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n"

        for url in ['/#/', '/#/submission']:
            data += "  <url>\n" + \
                    "    <loc>" + site + url + "</loc>\n" + \
                    "    <changefreq>weekly</changefreq>\n" + \
                    "    <priority>1.00</priority>\n"

            for lang in sorted(State.tenant_cache[1].languages_enabled):
                if lang != State.tenant_cache[1].default_language:
                    l = lang.lower()
                    l = l.replace('_', '-')
                    data += "<xhtml:link rel='alternate' hreflang='" + l + "' href='" + site + "/#/?lang=" + lang + "' />\n"

            data += "  </url>\n"

        data += "</urlset>"

        return data
