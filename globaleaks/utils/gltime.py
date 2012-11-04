# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

"""
Here is the location for all time and date related utility functions.
"""
import time
from datetime import datetime, timedelta

def utcDateNow():
    """
    Returns the datetime object of the current UTC time.
    """
    return datetime.utcnow()

def utcFutureDate(seconds=0, minutes=0, hours=0):
    """
    @param seconds: get a datetime obj with now+hours
    @param minutes: get a datetime obj with now+minutes
    @param hours: get a datetime obj with now+seconds
    @return: a datetime object
    """
    delta = (minutes * 60) + (hours * 3600) + seconds
    retTime = datetime.utcnow() + timedelta(seconds=delta)
    return retTime

def prettyDateTime(when):
    """
    @param when: a datetime like the stored DateTime in Storm
    @return: the pretty string
    """
    return when.ctime()

def utcTimeNow():
    """
    Returns seconds since epoch in UTC time, it's of type float.
    """
    return time.mktime(time.gmtime())

def dateToTime(date):
    """
    Takes as input a datetime object and outputs the seconds since epoch.
    """
    return time.mktime(date.timetuple())

def prettyDateNow():
    """
    Returns a good looking string for the local time.
    """
    return datetime.now().ctime()

def utcPrettyDateNow():
    """
    Returns a good looking string for utc time.
    """
    return datetime.utcnow().ctime()

def timeToPrettyDate(time_val):
    return time.ctime(time_val)
