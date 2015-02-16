# -*- encoding: utf-8 -*-

from twisted.internet import task, defer

from globaleaks.tests import helpers

from globaleaks import anomaly
from globaleaks.jobs import statistics_sched
from globaleaks.settings import GLSetting

anomaly.reactor = task.Clock()

def pollute_events_for_testing(number_of_times=1):
    for _ in xrange(number_of_times):
        for event_obj in anomaly.outcoming_event_monitored:

            for x in xrange(2):
                anomaly.EventTrack(event_obj, 1.0 * x)

class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """

    def test_event_accouting(self):

        anomaly.Alarm.compute_activity_level()

        # create one event per type.
        for event_obj in anomaly.outcoming_event_monitored:
            anomaly.EventTrack(event_obj, 1.0)

        x = anomaly.EventTrackQueue.take_current_snapshot()
        self.assertTrue(len(x) > 1)

    @defer.inlineCallbacks
    def test_compute_activity_level(self):
        """
        remind: activity level is called every 30 seconds by
        """
        pollute_events_for_testing()
        previous_len = len(anomaly.EventTrackQueue.take_current_snapshot())

        pollute_events_for_testing()
        self.assertEqual(len(
            anomaly.EventTrackQueue.take_current_snapshot()
        ), previous_len * 2)

        activity_level = yield anomaly.Alarm.compute_activity_level()
        self.assertEqual(activity_level, 2)

        # Has not slow comeback to 0
        activity_level = yield anomaly.Alarm.compute_activity_level()
        self.assertEqual(activity_level, 0)
