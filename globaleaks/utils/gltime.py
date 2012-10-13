import time
from datetime import datetime

def utcDateNow():
    return datetime.utcnow()

def utcTimeNow():
    return time.mktime(time.gmtime())

def dateToTime(date):
    return time.mktime(date.timetuple())
