# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import file
from globaleaks.tests import helpers


class TestFileInstance(helpers.TestHandler):
    _handler = file.FileInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(u'file.pdf')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(u'file.pdf')


class TestFileCollection(helpers.TestHandler):
    _handler = file.FileCollection

    @inlineCallbacks
    def test_get(self):
        self._handler = file.FileInstance
        handler = self.request({}, role='admin')
        yield handler.post(u'custom')

        self._handler = file.FileCollection
        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 1)

        self._handler = file.FileInstance
        handler = self.request({}, role='admin')
        yield handler.post(u'custom')

        handler = self.request({}, role='admin')
        yield handler.post(u'custom')

        self._handler = file.FileCollection
        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)
