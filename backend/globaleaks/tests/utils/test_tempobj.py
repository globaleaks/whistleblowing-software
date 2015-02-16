from twisted.trial import unittest
from twisted.internet import interfaces, task

from globaleaks.settings import GLSetting
from globaleaks.utils.tempobj import TempObj
from globaleaks.utils.utility import uuid4

class TestTempObj(unittest.TestCase):

    def test_object_creation_and_expiry(self):
        """
        creates two temporary objects and verify that they expire with the expected sequence
        reproduced the test pattern of twisted/test/test_task.py: testCallLater
        """

        c = task.Clock() # deterministic clock

        objs_dict = {}
        obj = {}

        for x in range(1, 4):
            obj[x] = TempObj(objs_dict, uuid4(), x, c)
            self.failUnless(interfaces.IDelayedCall.providedBy(obj[x]._expireCall))
            self.assertEqual(len(obj), x)

        y = len(obj)

        for x in range(1, 4):
            c.advance(1)
            self.assertEqual(len(objs_dict), y - x)


    def test_object_touch_and_expiry(self):
        """
        reproduced the test pattern of twisted/test/test_task.py: testCallLaterResetLater
        """

        c = task.Clock() # deterministic clock

        objs_dict = {}
        obj = TempObj(objs_dict, uuid4(), 2, c)
        obj.touch()
        c.advance(1)
        obj.touch()
        c.advance(1)
        obj.touch()
        c.advance(1)
        self.assertIsNotNone(obj._expireCall)
        c.advance(1)
        self.assertIsNone(obj._expireCall)

    def test_object_expire(self):
        """
        call the expire and checks that the object is expired
        """

        c = task.Clock() # deterministic clock

        objs_dict = {}
        obj = TempObj(objs_dict, uuid4(), 1, c)
        obj.expire()
        self.assertIsNone(obj._expireCall)

    def test_object_notifyOnExpire(self):
        """
        add 3 notifyOnExpire and checks that they are called
        """

        c = task.Clock() # deterministic clock

        events = []
        objs_dict = {}
        obj = TempObj(objs_dict, uuid4(), 2, c)

        for x in range(0, 3):
            obj.notifyOnExpire(lambda: events.append((x)))

        c.advance(1)

        self.assertEqual(0, len(events))

        c.advance(1)

        self.assertEqual(3, len(events))
