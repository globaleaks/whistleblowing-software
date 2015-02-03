# -*- coding: UTF-8
#
#   statistics
#   **********
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

import operator
from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc, And

from globaleaks.rest import errors, requests
from globaleaks.settings import transact_ro, transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, \
    authenticated
from globaleaks.jobs.statistics_sched import StatisticsSchedule
from globaleaks.models import Stats, Anomalies
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, \
    utc_past_date, iso_to_gregorian, log
from globaleaks.anomaly import EventTrackQueue, outcoming_event_monitored

def weekmap_to_heatmap(week_map):
    """
    convert a list of list with dict inside, in a flat list
    """
    retlist = []
    for weekday_n, weekday in enumerate(week_map):
        assert (weekday_n >= 0 and weekday_n <= 6), weekday_n
        for hour_n, hourinfo in enumerate(weekday):
            assert (hour_n >= 0 and hour_n <= 23), hour_n
            assert isinstance(hourinfo, dict), "Is not a dict in %d %d" % \
                                               (weekday_n, hour_n)
            retlist.append(hourinfo)

    return retlist

@transact_ro
def get_stats(store, week_delta):
    """
    :param week_delta: commonly is 0, mean that you're taking this
        week. -1 is the previous week.
    At the moment do not support negative number and change of the year.
    """

    now = datetime_now()
    week_delta = abs(week_delta)

    if week_delta > 0:
        # delta week in the past
        target_week = utc_past_date(hours=(week_delta * 24 * 7))
    else:
        # taking current time!
        target_week = datetime_now()

    looked_week = target_week.isocalendar()[1]
    looked_year = target_week.isocalendar()[0]

    current_wday = now.weekday()
    current_hour = now.hour
    current_week = now.isocalendar()[1]

    lower_bound = iso_to_gregorian(looked_year, looked_week, 1)
    upper_bound = iso_to_gregorian(looked_year, looked_week, 7)

    hourlyentries = store.find(Stats, And(Stats.start >= lower_bound, Stats.start <= upper_bound))

    week_entries = 0
    week_map = [[dict() for i in xrange(24)] for j in xrange(7)]

    # Loop over the DB stats to fill the appropriate heatmap
    for hourdata in hourlyentries:

        # .weekday() return be 0..6
        stats_day = int(hourdata.start.weekday())
        stats_hour = int(hourdata.start.isoformat()[11:13])

        hourly_dict = {
            'hour': stats_hour,
            'day': stats_day,
            'summary': hourdata.summary,
            'free_disk_space': hourdata.free_disk_space,
            'valid': 0  # 0 means valid data
        }

        if week_map[stats_day][stats_hour]:
            continue

        week_map[stats_day][stats_hour] = hourly_dict
        week_entries += 1

    # if all the hourly element are avail
    if week_entries == (7 * 24):
        return {
            'complete': True,
            'associated_date': datetime_to_ISO8601(target_week),
            'heatmap': weekmap_to_heatmap(week_map)
        }

    # else, supply default for the missing hour.
    # an hour can miss for two reason: the node was down (alarm)
    # or the hour is in the future (just don't display nothing)
    # -- this can be moved in the initialization phases ?
    for day in xrange(7):
        for hour in xrange(24):

            if week_map[day][hour]:
                continue

            # valid is used as status variable.
            # in the case the stats for the hour are missing it
            # assumes the following values:
            #  the hour is lacking from the results: -1
            #  the hour is in the future: -2
            #  the hour is the current hour (in the current day): -3
            if current_week != looked_week:
                marker = -1
            elif day > current_wday or \
                (day == current_wday and hour > current_hour):
                marker = -2
            elif current_wday == day and hour == current_hour:
                marker = -3
            else:
                marker = -1

            week_map[day][hour] = {
                'hour': hour,
                'day': day,
                'summary': {},
                'free_disk_space': 0,
                'valid': marker
            }

    return {
        'complete': False,
        'associated_date': datetime_to_ISO8601(target_week),
        'heatmap': weekmap_to_heatmap(week_map)
    }


@transact
def delete_weekstats_history(store):
    """
    Note: all the stats has to be in memory before being
        delete. In the long term this shall cause a memory exhaustion
    """

    allws = store.find(Stats)
    log.info("Deleting %d entries from hourly statistics table"
             % allws.count())

    allws.remove()

    # Now you're like a gringo without history, please invade Iraq
    log.info("Week statistics removal completed.")


@transact_ro
def get_anomaly_history(store, limit):
    anomal = store.find(Anomalies)
    anomal.order_by(Desc(Anomalies.creation_date))

    full_anomal = []
    for i, anom in enumerate(anomal):
        if limit == i:
            break
        anomaly_entry = dict({
            'when': anom.stored_when,
            'alarm': anom.alarm,
            'events': [],
        })
        for event_name, event_amount in anom.events.iteritems():
            anomaly_entry['events'].append({
                'name': event_name,
                'amount': event_amount,
            })
        full_anomal.append(anomaly_entry)

    return list(full_anomal)


@transact
def delete_anomaly_history(store):
    """
    Note: all the anomalies has to be in memory before being
        delete. In the long term this shall cause a memory exhaustion
    """

    allanom = store.find(Anomalies)
    log.info("Deleting %d entries from Anomalies History table"
             % allanom.count())

    allanom.remove()

    # Now you're like a child in the jungle
    log.info("Anomalies collection removal completed.")


class AnomaliesCollection(BaseHandler):
    """
    This Handler returns the list of the triggered anomalies based on
    activity monitored in a timedelta (is considered anomalous if they
    reach the thresholds defined in GLSettings)
    """

    @classmethod
    def update_AnomalyQ(cls, event_matrix, alarm_level):
        # called from statistics_sched
        date = datetime_to_ISO8601(datetime_now())[:-8]

        StatisticsSchedule.RecentAnomaliesQ.update({
            date: [event_matrix, alarm_level]
        })

    @transport_security_check("admin")
    @authenticated("admin")
    def get(self):
        """
        Anomalies history is track in Alarm, but is also stored in the
        DB in order to provide a good history.
        """
        self.finish(StatisticsSchedule.RecentAnomaliesQ)


class AnomalyHistoryCollection(BaseHandler):
    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def get(self):
        anomaly_history = yield get_anomaly_history(limit=20)
        self.finish(anomaly_history)

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def delete(self):
        log.info("Received anomalies history delete command")
        yield delete_anomaly_history()
        self.finish([])


class StatsCollection(BaseHandler):
    """
    This Handler returns the list of the stats, stats is the aggregated
    amount of activities recorded in the delta defined in GLSettings
    /admin/stats
    """

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def get(self, week_delta):
        week_delta = int(week_delta)

        if week_delta:
            log.debug("Asking statistics for %d weeks ago" % week_delta)
        else:
            log.debug("Asking statistics for current week")

        ret = yield get_stats(week_delta)

        self.finish(ret)

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def delete(self):
        log.info("Received statistic history delete command")
        yield delete_weekstats_history()
        self.finish([])


class RecentEventsCollection(BaseHandler):
    """
    This handler is refreshed constantly by an admin page
    and provide real time update about the GlobaLeaks status
    """

    @classmethod
    def update_RecentEventQ(cls, expired_event):
        """
        Called by synthesis in anomaly.py, when an Event expire.
        This mean that we have not the event for 59:30 minutes or
        less, but only the serialisation in memory.
        This is not show anyway.
        """
        date = datetime_to_ISO8601(expired_event.creation_date)[:-8]

        StatisticsSchedule.RecentEventQ.append(
            dict({
                'id': expired_event.event_id,
                'creation_date': date,
                'event':  expired_event.event_type,
                'duration': round(expired_event.request_time, 1),
            })
        )

    def get_summary(self, templist):
        eventmap = dict()
        for event in outcoming_event_monitored:
            eventmap.setdefault(event['name'], 0)

        for e in templist:
            eventmap[e['event']] += 1

        return eventmap

    @transport_security_check("admin")
    @authenticated("admin")
    def get(self, kind):
        templist = []

        # the current 30 seconds
        templist += EventTrackQueue.take_current_snapshot()
        # the already stocked by side, until Stats dump them in 1hour
        templist += StatisticsSchedule.RecentEventQ

        templist.sort(key=operator.itemgetter('id'))

        if kind == 'details':
            self.finish(templist)
        else:  # kind == 'summary':
            self.finish(self.get_summary(templist))
