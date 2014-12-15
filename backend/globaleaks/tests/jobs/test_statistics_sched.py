# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import anomaly
from globaleaks.tests import helpers

from globaleaks.jobs import statistics_sched

# E non e' la distanza ad abitare l'assenza.
# https://www.youtube.com/watch?v=UBdlNlDZDZA

# FIXME currenyly
# currently the following unit tests does not really perform complete
# unit tests and check but simply trigger the schedulers in order to
# raise the code coverage

class TestAnomaliesSchedule(helpers.TestGL):

    @inlineCallbacks
    def test_anomalies_schedule(self):
        yield statistics_sched.AnomaliesSchedule().operation()


class TestStaticsSchedule(helpers.TestGL):

    @inlineCallbacks
    def test_statistics_schedule(self):
        yield statistics_sched.StatisticsSchedule().operation()


class TestResourceCheckerSchedule(helpers.TestGL):

    @inlineCallbacks
    def test_resource_checker_schedule(self):
        yield statistics_sched.ResourceChecker().operation()
