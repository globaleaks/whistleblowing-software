# -*- coding: utf-8 -*
from globaleaks.tests import helpers
from globaleaks.utils.tempdict import TempDict


class TestObject(object):
    callbacks_count = 0

    def __init__(self, obj_id):
        self.id = obj_id

    def expireCallback(self):
        TestObject.callbacks_count += 1
        if self.id != TestObject.callbacks_count:
            raise Exception


class TestTempDict(helpers.TestGL):
    def test_timeout(self):
        timeout = 1337

        xxx = TempDict(timeout=timeout)

        for x in range(1, timeout + 1):
            xxx[x] = TestObject(x)
            self.assertEqual(len(xxx), x)
            self.test_reactor.advance(1)

        for x in range(1, timeout + 1):
            self.assertEqual(len(xxx), timeout - x)
            self.test_reactor.advance(1)

        self.assertEqual(len(xxx), 0)

        self.assertEqual(TestObject.callbacks_count, timeout)
