from twisted.trial import unittest

from txtorcon import log


class LoggingTests(unittest.TestCase):
    def test_debug(self):
        log.debug_logging()
