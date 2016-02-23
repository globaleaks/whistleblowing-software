from twisted.trial import unittest

from globaleaks.rest import api


class TestAPI(unittest.TestCase):
    def test_api_factory(self):
        api_factory = api.get_api_factory()
        # TODO: write some tests againg the API factory
