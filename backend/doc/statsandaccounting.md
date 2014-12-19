# Statistics and activity accounting

The event collection and reporting works in this way:

  * Every handler has an hook called prepare and finish, in those functions implemented in handlers/base.py there are some check about event accounting.
  * in anomaly.py there are two lists of event: incoming event and outcome event.
    * incoming event is check if the handler requested match and is created a temporay object.
    * outcome event is check handler and status code, ands is created an Event.

  * When needed, the event queueu the current event queue can be analized and the appropriate Alarm level can be determinated.
  * The Event window is set to 60 seconds, this mean that the event memory contains all the event happened in the latest 60 seconds.
  * The Event window can be dumped by the admin, accessing to a spefic REST API /admin/activities intended to show the recent activities.

  * When an Event expire (after 60 seconds) a short summary is written; this is called RecentEventQueue, and this queue is cleaned every 10 minutes.
  * Every 10 minutes the stats collection take the RecentEventQueue and flush it on the database.

  * Every 30 seconds a ResourceChecker routine is run; at the moment this routine monitors only the disk space with the aim to raise an alarm whenever the space is going to exausted (and this can eventually impair some upload or encryption activity)


The following is the detail on the periodic routines and it's executin time (implemented in statistic_sched.py):

  * AnomaliesSchedule, 30 seconds
  * ResourceChecker, 30 seconds
  * StatisticSchedule, 10 minutes


# GLBacken internal scheduler

## AnomaliesSchedule

Every 30 seconds is instanced an object of the class Alarm (anomaly.py) and 
is ask to compute the stress level based on the last 30 seconds window.

an Anomaly check the **stress level**, and stress level is measured with
value of **0**, **1**, **2**, visual color will be green, yellow, red.

Is evaluated when in the 30 second window between the first and the last, has a number of occurrence higher than expected.

At the moment the anomalies threshold are (defined in anomaly.py Alarm class)

  OUTCOME_ANOMALY_MAP = {
            'logins_failed': 5,
            'logins_successful': 3,
            'submissions_started': 5,
            'submissions_completed': 4,
            'wb_comments': 4,
            'wb_messages': 4,
            'uploaded_files': 11,
            'receiver_comments': 3,
            'receiver_messages': 3,
    }

There are two separated dictionary, because the OUTCOME and the INCOMING
are two separate hooks where the event accounting is recorded. At the
moment only the OUTCOME_ANOMALY is used, because is important associate
the time elapsed and the status error code in the Event collection.
INCOMING hook is present, not yet used.

When an event reach the threshold, the "activity stress level" is raised to 2 or 1.

  * if only one event-kind has reached anomaly threshold, alarm goes 1
  * if two or more event-kind has reached anomaly threshold, alarm goes 2
  * if the alarm was 2, and in the successive assessment the alarm can go to 0, still go to 1


## ResourceChecker

Is the job collecting the amount of free space in the disk, in order to keep
monitored the ability of the node to store uploaded material.

Also this checker raise another stress level, called 'disk stress level':

  * if the disk space is enough to receive up to 15 file upload of the maximum permitted size, the alarm is moved to 1
  * if the disk space is enough to receive up to 5 file upload of the maximum permitted size, the alarm is moved to 2


## StatisticSchedule

Every 10 minutes, all the collected event counters shift, are
summed and stored as activity statistics.

It make two operation:

  * take all the recent activities in the EventQueue, make a summary and record them for the statistics
  * take all the recent alarms raised, and save them in the *anomalies* table, to be conserved.

_After the Statistics, the queue are empty_, and therefore 'activities' and 'anomalies' REST API will return an empty list.

# Events monitoring signature definition

The kind of monitored event is dynamic, can be defined in the appropriate dictionary in anomaly.py:

    incoming_event_monitored = [
        {
            'name' : 'submission',
            'handler_check': submission_check,
            'anomaly_management': None,
            'method': 'POST'
        },


# REST API

### /admin/stats

Is a list, returning (internally locked) 20 elements, since the most recent.
Need to be defined the proper way to export a certain window time.

    {
        "day": 6, 
        "hour": 18,
        "week": 46, 
        "year": 2014
        "summary": {},
        "freemegabytes": 5666,
        "valid": 0
    }, 
    {
        "day": 6, 
        "hour": 19, 
        "week": 46, 
        "year": 2014,
        "summary": {
            "logins_failed": 28
        },
        "freemegabytes": 5627,
        "valid": 0
    }, 
    {
        "day": 6, 
        "hour": 20, 
        "week": 46, 
        "year": 2014,
        "summary": {
            "logins_failed": 61
        },
        "freemegabytes": 5618,
        "valid": 0
    }, 
    {
        "day": 1, 
        "hour": 1, 
        "week": 46, 
        "year": 2014,
        "summary": {},
        "freemegabytes": 0,
        "valid": 0
    }, 


the time is expressed in day, hour, week and year to facilitate heatmap visualisation.
summary may be empty because of no event, or because the box was down. if 
was down, the freemegabytes show -1, thus display with another color.

Is a list contains 7 * 24 precise entry every day. the summary is taken at the end of the hour (XX:00), if the box is down that moment, that hour stats get
lost. 

### /admin/anomalies

Current queue of alarm raised in the latest 10 minutes:

    {
    "2014-11-12T14:47:37": [
        {
            "submission": 39
        }, 
        1
    ] }

The key is the timedate (ISO8061 format, but without milliseconds because d3.js
used to display viz


### /admin/activities

Every time a new handlers, /admin/activities is called, the current logged 
events queue is copied and reported to the admin; this permits
realtime monitoring of the activities.

    "124": [
        "2014-11-12T14:29:18", 
        "comment"
    ], 
    "125": [
        "2014-11-12T14:29:18", 
        "comment"
    ], 
    "126": [
        "2014-11-12T14:29:19", 
        "comment"
    ], 
    "127": [
        "2014-11-12T14:29:20", 
        "submission"
    ], 
    "128": [
        "2014-11-12T14:29:20", 
        "comment"
    ], 

Every event has an incremental number, used as ID, and are collected the time of the event and the kind.

### /admin/history

With a query over /admin/history is possible extract the previous alarm collected:

    [ {
        "alarm": 2, 
        "events": {
            "comment": 15, 
            "login": 42
        }, 
        "when": "2014-11-12T01:28:29"
    }, 
    {
        "alarm": 1, 
        "events": {
            "submission": 43
        }, 
        "when": "2014-11-12T01:27:29"
    } ]


