# -*- coding: utf-8 -*-
from globaleaks.jobs import statistics
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

# FIXME
# currently the following unit tests does not really perform complete
# unit tests and check but simply trigger the schedulers in order to
# raise the code coverage


class TestStatics(helpers.TestGL):
    @inlineCallbacks
    def test_statistics(self):
        self.pollute_events(3)
        yield statistics.Statistics().run()
