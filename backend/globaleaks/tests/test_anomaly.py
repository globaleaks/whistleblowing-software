# -*- coding: utf-8 -*-
from datetime import timedelta

from globaleaks import event
from globaleaks.anomaly import Alarm
from globaleaks.tests import helpers
from twisted.internet import defer


class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """
    def test_event_accouting(self):
        Alarm.compute_activity_level()

        # create one event per type.
        for event_obj in event.events_monitored:
            event.EventTrack(event_obj, timedelta(seconds=1.0))

        x = event.EventTrackQueue.take_current_snapshot()
        self.assertTrue(len(x) > 1)

    @defer.inlineCallbacks
    def test_compute_activity_level(self):
        """
        remind: activity level is called every 30 seconds by
        """
        self.pollute_events()
        previous_len = len(event.EventTrackQueue.take_current_snapshot())

        self.pollute_events()
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
        self.pollute_events()
        activity_level = yield Alarm.compute_activity_level()
        self.assertEqual(activity_level, 2)

        yield Alarm.generate_admin_alert_mail(
            event_matrix = {
                'wb_comments': 100,
                'noise': 12345
            }
        )
