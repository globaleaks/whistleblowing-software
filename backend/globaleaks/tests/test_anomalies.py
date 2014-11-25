# -*- encoding: utf-8 -*-

from twisted.internet import task

from globaleaks.tests import helpers
from globaleaks.jobs import statistics_sched
from globaleaks.settings import GLSetting
from globaleaks import anomaly

anomaly.reactor = task.Clock()

class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """

    def test_event_accouting(self):

        a = anomaly.Alarm()
        a.compute_activity_level(notification=False)

        # create one event per type.
        for event_obj in anomaly.outcome_event_monitored:
            anomaly.EventTrack(event_obj, 1.0)

        x = anomaly.EventTrackQueue.take_current_snapshot()
        self.assertTrue(len(x) > 1)


    def test_token_difficulty(self):
        self.skipTest("Captcha difficulty implemented but not updated")

        a = anomaly.Alarm()

        self.assertEqual(anomaly.outcome_event_monitored[3]['name'], 'submission_completed')
        for x in xrange(100):
            # emulate 100 submission completed
            anomaly.EventTrack(anomaly.outcome_event_monitored[3], 0.0)

        d = a.compute_activity_level(notification=False)

        # adjust the stress_level and check if the expected behavior is placed
        anomaly.Alarm.stress_levels['activity'] = 1
        self.assertTrue(a.get_token_difficulty()['graph_captcha'])

        anomaly.Alarm.stress_levels['activity'] = 0
        self.assertFalse(a.get_token_difficulty()['graph_captcha'])

        anomaly.Alarm.stress_levels['disk_space'] = 1
        self.assertTrue(a.get_token_difficulty()['human_captcha'])

        anomaly.Alarm.stress_levels['disk_space'] = 0
        self.assertFalse(a.get_token_difficulty()['human_captcha'])


    def test_compute_activity_level(self):
        """
        remind: activity level is called every 30 seconds by
        """

        anomaly.EventTrackQueue.queue = dict()

        anomaly.pollute_Event_for_testing()
        previous_len = len(anomaly.EventTrackQueue.take_current_snapshot())

        anomaly.pollute_Event_for_testing()
        self.assertEqual(len(
            anomaly.EventTrackQueue.take_current_snapshot()
        ), previous_len * 2)

        activity_level = anomaly.Alarm().compute_activity_level(notification=False)
        description = anomaly.Alarm().get_description_status()
        self.assertEqual(activity_level, 2)

        # Has not slow comeback to 0
        activity_level = anomaly.Alarm().compute_activity_level(notification=False)
        self.assertEqual(activity_level, 0)

