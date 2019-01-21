# -*- coding: utf-8 -*-
#
# Implementation of sitemap resource
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks.state import State


class SitemapHandler(BaseHandler):
    check_roles = '*'

    def get(self):
        """
        Get the sitemap.xml
        """
        if not State.tenant_cache[self.request.tid].allow_indexing:
            raise errors.ResourceNotFound()

        self.request.setHeader(b'Content-Type', b'text/xml')

        data = "<?xml version='1.0' encoding='UTF-8' ?>\n" + \
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n"

        tids = [self.request.tid]
        if self.request.tid == 1:
            tids = State.tenant_cache.keys()

        for tid in tids:
            urls = ['/#/']

            site = 'https://' + State.tenant_cache[tid].hostname

            if tid == 1 and State.tenant_cache[1].enable_signup:
                urls.append('/#/signup')
            else:
                urls.append('/#/submission')

            for url in urls:
                data += "  <url>\n" + \
                        "    <loc>" + site + url + "</loc>\n" + \
                        "    <changefreq>weekly</changefreq>\n" + \
                        "    <priority>1.00</priority>\n"

                for lang in sorted(State.tenant_cache[tid].languages_enabled):
                    if lang != State.tenant_cache[tid].default_language:
                        l = lang.lower()
                        l = l.replace('_', '-')
                        data += "<xhtml:link rel='alternate' hreflang='" + l + "' href='" + site + url + "?lang=" + lang + "' />\n"

                data += "  </url>\n"

        data += "</urlset>"

        return data
