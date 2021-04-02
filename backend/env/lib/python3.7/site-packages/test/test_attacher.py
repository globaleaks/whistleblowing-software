from mock import Mock
from zope.interface import directlyProvides

from twisted.trial import unittest

from txtorcon.attacher import PriorityAttacher
from txtorcon.interface import IStreamAttacher


class PriorityAttacherTest(unittest.TestCase):

    def test_add_remove(self):
        a = PriorityAttacher()
        boom = Mock()
        directlyProvides(boom, IStreamAttacher)

        a.add_attacher(boom)
        a.remove_attacher(boom)
        with self.assertRaises(ValueError) as ctx:
            a.remove_attacher(boom)
        self.assertTrue('not found' in str(ctx.exception))

    def test_stream_failure(self):
        a = PriorityAttacher()
        boom = Mock()
        directlyProvides(boom, IStreamAttacher)

        a.add_attacher(boom)
        a.attach_stream_failure(Mock(), Mock())

    def test_attach_stream(self):
        a = PriorityAttacher()
        boom = Mock()
        directlyProvides(boom, IStreamAttacher)

        a.add_attacher(boom)
        a.attach_stream(Mock(), [])

    def test_attach_stream_nothing(self):
        a = PriorityAttacher()
        a.attach_stream(Mock(), [])
