# -*- encoding: utf-8 -*-

from twisted.internet import task, defer

from globaleaks.tests import helpers

from globaleaks import event
from globaleaks.anomaly import Alarm


def pollute_events_for_testing(number_of_times=10):
    for _ in xrange(number_of_times):
        for event_obj in event.events_monitored:
            for x in xrange(2):
                event.EventTrack(event_obj, 1.0 * x)


def pollute_events_for_testing_and_perform_synthesis(number_of_times=10):
    for _ in xrange(number_of_times):
        for event_obj in event.events_monitored:
            for x in xrange(2):
                event.EventTrack(event_obj, 1.0 * x).synthesis()


class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """
    def test_event_accouting(self):
        Alarm.compute_activity_level()

        # create one event per type.
        for event_obj in event.events_monitored:
            event.EventTrack(event_obj, 1.0)

        x = event.EventTrackQueue.take_current_snapshot()
        self.assertTrue(len(x) > 1)

    @defer.inlineCallbacks
    def test_compute_activity_level(self):
        """
        remind: activity level is called every 30 seconds by
        """
        pollute_events_for_testing()
        previous_len = len(event.EventTrackQueue.take_current_snapshot())

        pollute_events_for_testing()
        self.assertEqual(len(
            event.EventTrackQueue.take_current_snapshot()
        ), previous_len * 2)

        activity_level = yield Alarm.compute_activity_level()
        self.assertEqual(activity_level, 2)

        # Has not slow comeback to 0
        activity_level = yield Alarm.compute_activity_level()
        self.assertEqual(activity_level, 0)


class TestAnomalyNotification(helpers.TestGL):
    @defer.inlineCallbacks
    def test_generate_admin_alert_mail(self):
        # Remind, these two has to be done to get an event matrix meaningful
        pollute_events_for_testing()
        activity_level = yield Alarm.compute_activity_level()

        x = yield Alarm.generate_admin_alert_mail(
            event_matrix = {
                'wb_comments': 100,
                'noise': 12345
            }
        )
