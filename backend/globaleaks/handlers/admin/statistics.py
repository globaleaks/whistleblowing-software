#/a -*- coding: utf-8
#
#   statistics
#   **********
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.
import operator
from datetime import timedelta
from storm.expr import Desc, And

from globaleaks.state import State
from globaleaks.event import EventTrackQueue, events_monitored
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Stats, Anomalies
from globaleaks.orm import transact
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, \
    iso_to_gregorian


def weekmap_to_heatmap(week_map):
    """
    convert a list of list with dict inside, in a flat list
    """
    retlist = []
    for _, weekday in enumerate(week_map):
        for _, hourinfo in enumerate(weekday):
            retlist.append(hourinfo)

    return retlist


@transact
def get_stats(store, tid, week_delta):
    """
    :param week_delta: commonly is 0, mean that you're taking this
        week. -1 is the previous week.
    At the moment do not support negative number and change of the year.
    """
    now = datetime_now()
    week_delta = abs(int(week_delta))

    target_week = datetime_now()
    if week_delta > 0:
        # delta week in the past
        target_week -= timedelta(hours=week_delta * 24 * 7)

    looked_week = target_week.isocalendar()[1]
    looked_year = target_week.isocalendar()[0]

    current_wday = now.weekday()
    current_hour = now.hour
    current_week = now.isocalendar()[1]

    lower_bound = iso_to_gregorian(looked_year, looked_week, 1)
    upper_bound = iso_to_gregorian(looked_year, looked_week + 1, 1)

    hourlyentries = store.find(Stats, Stats.tid == tid, And(Stats.start >= lower_bound, Stats.start <= upper_bound))

    week_entries = 0
    week_map = [[dict() for i in range(24)] for j in range(7)]

    # Loop over the DB stats to fill the appropriate heatmap
    for hourdata in hourlyentries:
        # .weekday() return be 0..6
        stats_day = int(hourdata.start.weekday())
        stats_hour = int(hourdata.start.isoformat()[11:13])

        week_map[stats_day][stats_hour] = {
            'hour': stats_hour,
            'day': stats_day,
            'summary': hourdata.summary,
            'free_disk_space': hourdata.free_disk_space,
            'valid': 0  # 0 means valid data
        }

        week_entries += 1

    # if all the hourly element is available
    if week_entries != (7 * 24):
        for day in range(7):
            for hour in range(24):
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
        'complete': week_entries == (7 * 24),
        'week': datetime_to_ISO8601(target_week),
        'heatmap': weekmap_to_heatmap(week_map)
    }


@transact
def get_anomaly_history(store, limit):
    anomalies = store.find(Anomalies).order_by(Desc(Anomalies.date))[:limit]

    anomaly_history = []
    for _, anomaly in enumerate(anomalies):
        anomaly_entry = dict({
            'date': datetime_to_ISO8601(anomaly.date),
            'alarm': anomaly.alarm,
            'events': [],
        })
        for event_type, event_count in anomaly.events.items():
            anomaly_entry['events'].append({
                'type': event_type,
                'count': event_count,
            })
        anomaly_history.append(anomaly_entry)

    return anomaly_history


class AnomalyCollection(BaseHandler):
    check_roles = 'admin'

    def get(self):
        return get_anomaly_history(limit=20)


class StatsCollection(BaseHandler):
    """
    This Handler returns the list of the stats for the requested range
    """
    check_roles = 'admin'

    def get(self, week_delta):
        return get_stats(self.request.tid, week_delta)


class RecentEventsCollection(BaseHandler):
    """
    This handler is refreshed constantly by an admin page
    and provide real time update about the GlobaLeaks status
    """
    check_roles = 'admin'

    def get_summary(self, templist):
        eventmap = dict()
        for event in events_monitored:
            eventmap.setdefault(event['name'], 0)

        for e in templist:
            eventmap[e['event']] += 1

        return eventmap

    def get(self, kind):
        templist = []

        # the current 30 seconds
        templist += EventTrackQueue.take_current_snapshot()
        # the already stocked by side, until Stats dump them in 1hour
        templist += State.RecentEventQ

        templist.sort(key=operator.itemgetter('id'))

        if kind == 'details':
            return templist

        return self.get_summary(templist)


class JobsTiming(BaseHandler):
    """
    This handler return the timing for the latest scheduler execution
    """
    check_roles = 'admin'

    def get(self):
        response = []

        for job in State.jobs:
            response.append({
              'name': job.name,
              'timings': job.last_executions
            })

        return response
