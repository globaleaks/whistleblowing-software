# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

"""
Here is the location for all time and date related utility functions.
"""
import time
from datetime import datetime

def utcDateNow():
    """
    Returns the datetime object of the current UTC time.
    """
    return datetime.utcnow()

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

