# -*- encoding: utf-8 -*-

from twisted.internet import task, defer

from globaleaks.tests import helpers

from globaleaks import anomaly, event

anomaly.reactor = task.Clock()

def pollute_events_for_testing(number_of_times=10):
    for _ in xrange(number_of_times):
        for event_obj in event.outcoming_event_monitored:
            for x in xrange(2):
                event.EventTrack(event_obj, 1.0 * x)

class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """

    def test_event_accouting(self):

        anomaly.compute_activity_level()

        # create one event per type.
        for event_obj in event.outcoming_event_monitored:
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

        activity_level = yield anomaly.compute_activity_level()
        self.assertEqual(activity_level, 2)

        # Has not slow comeback to 0
        activity_level = yield anomaly.compute_activity_level()
        self.assertEqual(activity_level, 0)

class TestAnomalyNotification(helpers.TestGL):

    @defer.inlineCallbacks
    def test_admin_alarm_generate_mail(self):
        a = anomaly.Alarm()

        # Remind, these two has to be done to get an event matrix meaningful
        pollute_events_for_testing()
        activity_level = yield anomaly.compute_activity_level()

        x = yield a.admin_alarm_generate_mail(
            event_matrix= {
                'wb_comments': 100,
                'noise': 12345
            }
        )
