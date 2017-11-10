# uncompyle6 version 2.11.5
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Nov 19 2016, 06:48:10) 
# [GCC 5.4.0 20160609]
# Embedded file name: /home/evilaliv3/Devel/GlobaLeaks/backend/globaleaks/tests/test_anomaly.py
# Compiled at: 2017-11-10 12:04:32
from datetime import timedelta
from globaleaks import event
from globaleaks.anomaly import Alarm
from globaleaks.tests import helpers
from twisted.internet import defer

class TestAlarm(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """

    @defer.inlineCallbacks
    def test_compute_activity_level(self):
        """
        remind: activity level is called every 30 seconds by
        """
        self.pollute_events()

        activity_level = yield Alarm.compute_activity_level()

        self.assertEqual(activity_level, 2)

        activity_level = yield Alarm.compute_activity_level()

        self.assertEqual(activity_level, 0)


class TestAnomalyNotification(helpers.TestGL):

    @defer.inlineCallbacks
    def test_generate_admin_alert_mail(self):
        self.pollute_events()

        activity_level = yield Alarm.compute_activity_level()

        self.assertEqual(activity_level, 2)

        yield Alarm.generate_admin_alert_mail(event_matrix={'wb_comments': 100,'noise': 12345})
