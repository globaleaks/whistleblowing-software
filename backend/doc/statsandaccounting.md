# Statistics and activity accounting

The event collection and reporting works in this way:

  * Every handler has an hook called prepare and finish, in those functions implemented in handlers/base.py there are some check about event accounting.
  * At a periodic time event queue is analized and the appropriate Alarm Level is determinated.
  * The Event window is set to 60 seconds, this mean that the event memory contains all the event happened in the latest 60 seconds.
  * The current event queue can be exported by the admin, accessing to a spefic REST API /admin/activities intended to show the recent activities.
  * When an Event expire (after 60 seconds) a short summary is written; this is called RecentEventQueue.
  * Every hour the stats collection take the RecentEventQueue and flush it on the database.

The following is the detail on the periodic routines and their executing time (implemented in statistic_sched.py):

  * AnomaliesSchedule, 30 seconds
  * StatisticSchedule, 1 hour

# GLBackend internal scheduler

## AnomaliesSchedule (HANDLERS CHECK)

Every 30 seconds is instanced an object of the class Alarm (anomaly.py) and 
is ask to compute the stress level based on the last 30 seconds window.

an Anomaly check the **stress level**, and stress level is measured with
value of **0**, **1**, **2**, visual color will be green, yellow, red.

Is evaluated when in the 30 second window between the first and the last, has a number of occurrence higher than expected.

At the moment the anomalies threshold are (defined in anomaly.py Alarm class)

    ANOMALY_MAP = {
        'failed_logins': 5,
        'successful_logins': 3,
        'started_submissions': 5,
        'completed_submissions': 4,
        'failed_submissions': 5,
        'files': 10,
        'comments': 30,
        'messages': 30
    }

When an event reach the threshold, the "activity stress level" is raised to 2 or 1.

  * if only one event-kind has reached anomaly threshold, alarm goes 1
  * if two or more event-kind has reached anomaly threshold, alarm goes 2
  * if the alarm was 2, and in the successive assessment the alarm can go to 0, still go to 1

## AnomaliesSchedule (DISK SPACE CHECK)

Is the job collecting the amount of free space in the disk, in order to keep
monitored the ability of the node to store uploaded material.

Also this checker raise another stress level, called 'disk stress level':

  * if the disk space is enough to receive up to 15 file upload of the maximum permitted size, the alarm is moved to 1
  * if the disk space is enough to receive up to 5 file upload of the maximum permitted size, the alarm is moved to 2


## StatisticSchedule

Every hour all the collected event counters are collected and stored as activity statistics.

The scheduler makes two operations:

  * it takes all the recent activities in the EventQueue, make a summary and record them for the statistics
  * it takes all the recent alarms raised, and save them in the *anomalies* table, to be conserved.

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
        "summary": {},
        "free_disk_space": 5666,
        "valid": 0
    }, 
    {
        "day": 6, 
        "hour": 19, 
        "summary": {
            "failed_logins": 28
        },
        "free_disk_space": 5627,
        "valid": 0
    }, 
    {
        "day": 6, 
        "hour": 20, 
        "summary": {
            "failed_logins": 61
        },
        "freemegabytes": 5618,
        "valid": 0
    }, 
    {
        "day": 1, 
        "hour": 1, 
        "summary": {},
        "free_disk_space": 0,
        "valid": 0
    }, ...

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
        }, ...
      ]
    }

### /admin/activities

Every time /admin/activities handler is requested the current logged 
events queue is copied and reported to the admin; this enables realtime
monitoring of the activities.

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
    ], ... 

Every event has an incremental number, used as ID, and are collected the time of the event and the kind.

### /admin/anomalies

The handler /admin/anomalies exports the previous alarms collected:

    [
      {
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
      }
    ]
