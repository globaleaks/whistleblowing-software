# -*- coding: UTF-8
# public
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.handlers.admin.files import db_get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import l10n
from globaleaks.models.config import NodeFactory
from globaleaks.models.l10n import NodeL10NFactory
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.sets import disjoint_union
from globaleaks.utils.structures import get_localized_values


class RobotstxtHandler(BaseHandler):
    @BaseHandler.transport_security_check("unauth")
    @BaseHandler.unauthenticated
    def get(self):
        """
        Get the robots.txt
        """
        self.set_header('Content-Type', 'text/plain')

        self.write("User-agent: *\n")
        self.write("Allow: /" if GLSettings.memory_copy.allow_indexing else "Disallow: /")


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
                   "<urlset\n" +
                   "         xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'\n" +
                   "         xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'\n" +
                   "         xsi:schemaLocation='http://www.sitemaps.org/schemas/sitemap/0.9\n" +
                   "         http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd'>\n" +
                   "  <url>\n" +
                   "    <loc>" + GLSettings.memory_copy.public_site + "/</loc>\n" +
                   "    <changefreq>weekly</changefreq>\n" +
                   "    <priority>1.00</priority>\n" +
                   "  </url>\n" +
                   "  <url>\n" +
                   "    <loc>" + GLSettings.memory_copy.public_site + "/#/submission</loc>\n" +
                   "    <changefreq>weekly</changefreq>\n" +
                   "    <priority>1.00</priority>\n" +
                   "  </url>\n" +
                   "</urlset>")
