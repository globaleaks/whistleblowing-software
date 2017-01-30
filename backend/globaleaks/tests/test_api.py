from globaleaks.tests.helpers import TestGL

class TestAPI(TestGL):
    def test_api_factory(self):
        from globaleaks.rest import api
        api.get_api_factory()
        # TODO: write some tests againg the API factory
