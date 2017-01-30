# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import public
from globaleaks.models import config
from globaleaks.rest import requests
from globaleaks.tests import helpers


class TestPublicResource(helpers.TestHandlerWithPopulatedDB):
    _handler = public.PublicResource

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        yield handler.get()

        resp_desc = self.ss_serial_desc(config.NodeFactory.public_node, requests.PublicResourcesDesc)
        self._handler.validate_message(json.dumps(self.responses[0]), resp_desc)
