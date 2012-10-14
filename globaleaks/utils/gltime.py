import time
from datetime import datetime

def utcDateNow():
    return datetime.utcnow()

def utcTimeNow():
    return time.mktime(time.gmtime())

def dateToTime(date):
    return time.mktime(date.timetuple())

def prettyDateNow():
    return datetime.now().ctime()

def utcPrettyDateNow():
    return datetime.utcnow().ctime()

