# -*- coding: utf-8 -*-
from globaleaks.handlers.admin import context
from globaleaks.models import Context
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

class TestContextsCollection(helpers.TestCollectionHandler):
    _handler = context.ContextsCollection
    _test_desc = {
      'model': Context,
      'create': context.create_context,
      'data': {
          'tip_timetolive': 100
      }
    }


class TestContextInstance(helpers.TestInstanceHandler):
    _handler = context.ContextInstance
    _test_desc = {
      'model': Context,
      'create': context.create_context,
      'data': {
          'tip_timetolive': 100
      }
    }
