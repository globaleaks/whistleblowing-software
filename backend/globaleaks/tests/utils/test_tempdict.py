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
        size_limit = 1000000

        xxx = TempDict(timeout=timeout, size_limit=size_limit)

        xxx.expireCallback = expireCallback

        for x in range(1, timeout + 1):
            xxx.set(x, TestObject(x))
            self.assertEqual(len(xxx), x)
            self.test_reactor.advance(1)

        for x in range(1, timeout + 1):
            self.assertEqual(len(xxx), timeout - x)
            self.test_reactor.advance(1)

        self.assertEqual(len(xxx), 0)

        self.assertEqual(TestObject.callbacks_count, timeout)

    def test_size_limit(self):
        timeout = 666
        size_limit = 666

        xxx = TempDict(timeout=timeout, size_limit=size_limit)

        for x in range(1, size_limit * 2):
            xxx.set(x, TestObject(x))
            if x < size_limit:
                self.assertEqual(len(xxx), x)
                self.assertEqual(xxx.get(x).id, x)
                self.assertEqual(xxx.get(x + 1), None)
            else:
                self.assertEqual(len(xxx), size_limit)
                self.assertEqual(xxx.get(x - size_limit + 1).id, x - size_limit + 1)
                self.assertEqual(xxx.get(x - size_limit), None)
