# -*- coding: utf-8 -*-

from twisted.internet.defer import fail
from twisted.web.client import getPage

try:
    from twisted.web.client import URI
except ImportError:
    from twisted.web.client import _URI as URI

from globaleaks.utils import tls

def getPageSecurely(url):
    try:
        parsed_url=URI.fromBytes(url)

        if parsed_url.scheme != 'https':
            return fail()

        return getPage(url, tls.TLSClientContextFactory(parsed_url.host))

    except:
        return fail()
