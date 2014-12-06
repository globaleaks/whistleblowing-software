# -*- coding: UTF-8
#
#   statistics
#   **********
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

import operator
from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.rest import errors
from globaleaks.settings import transact_ro, transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.models import WeekStats, Anomalies
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, log
from globaleaks.anomaly import EventTrackQueue, outcome_event_monitored, pollute_Event_for_testing

@transact_ro
def get_stats(store, delta_week):
    """
    :param delta_week: commonly is 0, mean that you're taking this
        week. -1 is the previous week.
    At the moment do not support negative number and change of the year.
    """

    target_week = int(datetime_now().isocalendar()[1]) - delta_week

    hourlyentry = store.find(WeekStats)

    week_stats = []
    last_stats_dict = {}

    for hourdata in hourlyentry:

        # This need to be optimized at store.find level
        if int(hourdata.start.isocalendar()[1]) != target_week:
            continue

        last_stats_dict = {
            'summary' : hourdata.summary,
            'year' : int(hourdata.start.isocalendar()[0]),
            'week' :  int(hourdata.start.isocalendar()[1]),
            'hour' : int(hourdata.start.isoformat()[11:13]),
            'day' : int(hourdata.start.isocalendar()[2]),
            'freemegabytes' : hourdata.freemb,
        }
        week_stats.append(last_stats_dict)

    # if all the hourly element are avail
    if len(week_stats) == (7 * 24):
        return list(week_stats)

    # if none of the hourly element are avail
    if not len(week_stats):
        last_stats_dict['year'] = datetime_now().year

    # else, supply default for the missing hour
    for day in xrange(1, 8):
        for hour in xrange(1, 25):

            missing_hour = True
            for hs in week_stats:
                if hs['day'] == day and hs['hour'] == hour:
                    missing_hour = False

            if not missing_hour:
                continue

            week_stats.append({
                'summary': {},
                'year': last_stats_dict['year'],
                'week': target_week,
                'hour': hour,
                'day': day,
                'freemegabytes': -1,
            })

    return list(week_stats)


@transact
def delete_weekstats_history(store):
    """
    Note: all the stats has to be in memory before being
        delete. In the long term this shall cause a memory exhaustion
    """

    allws = store.find(WeekStats)
    log.info("Deleting %d entries from hourly statistics table" % allws.count())
    for ws in allws:
        store.remove(ws)

    # I'll put store.commit() here to check the amount of seconds between
    # the previous and the next log entry. is redundant anyway because @transact
    # supply.
    store.commit()
    log.info("Week statistics removal complete. Now you're like a gringo without history, please invade Iraq")


@transact_ro
def get_anomaly_history(store, limit):

    anomal = store.find(Anomalies)
    anomal.order_by(Desc(Anomalies.creation_date))

    full_anomal = []
    for i, anom in enumerate(anomal):
        if limit == i:
            break
        anomaly_entry = dict({
            'when' : anom.stored_when,
            'alarm' : anom.alarm,
            'events': [],
        })
        for event_name, event_amount in anom.events.iteritems():
            anomaly_entry['events'].append({
                'name' : event_name,
                'amount' : event_amount,
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
    log.info("Deleting %d entries from Anomalies History table" % allanom.count())
    for anom in allanom:
        store.remove(anom)

    # I'll put store.commit() here to check the amount of seconds between
    # the previous and the next log entry. is redundant anyway because @transact
    # supply.
    store.commit()
    log.info("Anomalies collection removal complete. Now you're like a child in the jungle")


class AnomaliesCollection(BaseHandler):
    """
    This Handler returns the list of the triggered anomalies based on
    activity monitored in a timedelta (is considered anomalous if they
    reach the thresholds defined in GLSettings)
    """

    # This is a class level var that collect the latest anomalies collected.
    # Every 10 minutes they are flushed out in the statistics
    RecentAnomaliesQ = {}

    @classmethod
    def update_AnomalyQ(cls, event_matrix, alarm_level):
        # called from statistics_sched
        AnomaliesCollection.RecentAnomaliesQ.update({
            datetime_to_ISO8601(datetime_now())[:-8] :
                [ event_matrix, alarm_level ]
        })


    @transport_security_check("admin")
    @authenticated("admin")
    def get(self, *uriargs):
        """
        Anomalies history is track in Alarm, but is also stored in the
        DB in order to provide a good history.
        """
        self.finish(AnomaliesCollection.RecentAnomaliesQ)

class AnomalyHistoryCollection(BaseHandler):

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def get(self, *uriargs):

        anomaly_history = yield get_anomaly_history(limit=20)
        self.finish(anomaly_history)

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def delete(self, *uriargs):

        log.info("Anoalies history delete command received!")
        yield delete_anomaly_history()
        self.set_status(200)



class StatsCollection(BaseHandler):
    """
    This Handler returns the list of the stats, stats is the aggregated amount of
    activities recorded in the delta defined in GLSettings
    /admin/stats
    """

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def get(self, weeks_in_the_past):

        proper_delta = (int(weeks_in_the_past) * -1)
        if proper_delta:
            log.debug("Asking statistics for %d weeks ago" % proper_delta)
        else:
            log.debug("Asking statistics for this week")

        stats_block = yield get_stats(proper_delta)
        self.finish(stats_block)


    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def delete(self, *uriargs):

        log.info("Statistic delete command received!")
        yield delete_weekstats_history()
        self.set_status(200)



class RecentEventsCollection(BaseHandler):
    """
    This handler is refreshed constantly by an admin page
    and provide real time update about the GlobaLeaks status
    """

    # This is a class variable that collect the last 0 to 10 minutes of events.
    # Every 10 minutes is flushed in the statistics
    RecentEventQueue = []

    @classmethod
    def update_RecentEventQ(cls, expired_event):
        """
        Called by synthesis in anomaly.py, when an Event expire.
        This mean that we have not the event for 59:30 minutes or
        less, but only the serialisation in memory.
        This is not show anyway.
        """

        RecentEventsCollection.RecentEventQueue.append(dict({
            'id' : expired_event.event_id,
            'creation_date' : datetime_to_ISO8601(expired_event.creation_date)[:-8],
            'event' :  expired_event.event_type,
            'duration' : round(expired_event.request_time, 1),
            })
        )

    def print_bubble(self, templist):
        """
        This visualisation output is not used ATM
        """

        eventmap = dict()
        for event in outcome_event_monitored:
            eventmap.setdefault(event['name'], 0)

        # TODO make a sum/mix/man/all the timings ?
        for e in templist:
            eventmap[e['event']] += 1

        retdict = {
            "name": 'Node recent activities',
            "children": [
                {
                    'name': 'login',
                    'children' : [
                        { 'name': 'success', 'size': eventmap['login_success'] },
                        { 'name': 'failure', 'size': eventmap['login_failure'] },
                        ]
                },
                {
                    'name': 'submission',
                    'children' : [
                        { 'name': 'started', 'size': eventmap['submission_started']},
                        { 'name': 'completed', 'size': eventmap['submission_completed']},
                        ]
                },
                { 'name' : 'wb_comment', 'size': eventmap['wb_comment'] },
                { 'name' : 'file', 'size': eventmap['file'] }
            ]
        }
        return retdict

    def get_summary(self, templist):

        eventmap = dict()
        for event in outcome_event_monitored:
            eventmap.setdefault(event['name'], 0)

        for e in templist:
            eventmap[e['event']] += 1

        return eventmap


    @transport_security_check("admin")
    @authenticated("admin")
    def get(self, kind, *uriargs):

        if not kind in [ 'bubble', 'details', 'summary' ]:
            raise errors.InvalidInputFormat(kind)

        templist = []

        # the current 30 seconds
        templist += EventTrackQueue.take_current_snapshot()
        # the already stocked by side, until Stats dump them in 1hour
        templist += RecentEventsCollection.RecentEventQueue

        templist.sort(key=operator.itemgetter('id'))

        if kind == 'bubble':
            self.finish(
                self.print_bubble(templist)
            )
        elif kind == 'details':
            self.finish(templist)
        else: # summary
            self.finish(self.get_summary(templist))

