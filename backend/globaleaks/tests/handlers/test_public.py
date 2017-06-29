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
        response = yield handler.get()

        self._handler.validate_message(json.dumps(response), requests.PublicResourcesDesc)
