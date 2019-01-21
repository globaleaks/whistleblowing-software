# -*- coding: utf-8
#   utility
#   *******
#
# Utility Functions
from __future__ import print_function

import glob
import io
import json
import os
import platform
import re
import uuid
from datetime import datetime, timedelta
from six import text_type, binary_type

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.log import log


def get_disk_space(path):
    if platform.system() != 'Windows':
        statvfs = os.statvfs(path)
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        total_bytes = statvfs.f_frsize * statvfs.f_blocks

        return free_bytes, total_bytes
    else:
        # statvfs not available on Windows; the only way to get it
        # without a new pypi dependency is to invoke ctypes voodoo
        import ctypes

        abs_path = os.path.abspath(path)
        dir_path = os.path.dirname(abs_path)

        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)

        # GetDiskFreeSpaceEx expects a directory path, and returns two
        # pointers with the necessary information
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(dir_path),
            None,
            ctypes.pointer(total_bytes),
            ctypes.pointer(free_bytes))

        return free_bytes.value, total_bytes.value


def read_file(p):
    with io.open(p, 'r', encoding='utf-8') as f:
        return f.read().rstrip("\n")


def read_json_file(p):
    return json.loads(read_file(p))


def drop_privileges(user, uid, gid):
    if platform.system() != 'Windows':
        if os.getgid() != gid:
            os.setgid(gid)
            os.initgroups(user, gid)

        if os.getuid() != uid:
            os.setuid(uid)
    else:
        log.err("Unable to securely drop permissions on Windows")


def fix_file_permissions(path, uid, gid, dchmod, fchmod):
    """
    Recursively fix file permissions on a given path
    """
    def fix(path):
        if platform.system() != 'Windows':
            os.chown(path, uid, gid)
            if os.path.isfile(path):
                os.chmod(path, 0o600)
            else:
                os.chmod(path, 0o700)
        else:
            log.err("Unable to secure %s on Windows", path)

    fix(path)
    for item in glob.glob(path + '/*'):
        fix_file_permissions(item, uid, gid, dchmod, fchmod)


def uuid4():
    """
    This function returns a uuid4.

    The function is not intended to be used for security reasons.
    """
    return text_type(uuid.uuid4())


def sum_dicts(*dicts):
    ret = {}

    for d in dicts:
        for k, v in d.items():
            ret[k] = v

    return ret


def every_language_dict(default_text=''):
    return {code: default_text for code in LANGUAGES_SUPPORTED_CODES}


def deferred_sleep(timeout):
    d = Deferred()

    reactor.callLater(timeout, d.callback, True)

    return d


def msdos_encode(s):
    """
    This functions returns a new string with all occurences of newlines
    preprended with a carriage return.
    """
    return re.sub(r'(\r\n)|(\n)', '\r\n', s)


def iso_strf_time(d):
    return d.strftime("%Y-%m-%d %H:%M:%S.%f")


def datetime_null():
    """
    @return: a utc datetime object representing a null date
    """
    return datetime(1970, 1, 1, 0, 0)


def datetime_now():
    """
    @return: a utc datetime object for the current time
    """
    return datetime.utcnow()


def datetime_never():
    """
    @return: a utc datetime object representing the 1st January 3000
    """
    return datetime(3000, 1, 1, 0, 0)


def get_expiration(days):
    """
    @return: a utc datetime object representing an expiration time calculated as the current date + N days
    """
    date = datetime.utcnow()
    return datetime(year=date.year, month=date.month, day=date.day, hour=00, minute=00, second=00) + timedelta(days=days+1)


def is_expired(check_date, seconds=0, minutes=0, hours=0, days=0):
    """
    @param check_date: a datetime or a timestap
    @param seconds, minutes, hours, day
        the time to live of the element
    @return:
        if now > check_date + (seconds+minutes+hours)
        True is returned, else False
    """
    total_hours = (days * 24) + hours
    check = check_date + timedelta(seconds=seconds, minutes=minutes, hours=total_hours)

    return datetime_now() > check


def datetime_to_ISO8601(date):
    """
    conver a datetime into ISO8601 date
    """
    if date is None:
        date = datetime_null()

    return date.isoformat() + "Z"  # Z means that the date is in UTC


def ISO8601_to_datetime(isodate):
    """
    convert an ISO8601 date into a datetime
    """
    isodate = isodate[:19]  # we srip the eventual Z at the end

    return datetime.strptime(isodate, "%Y-%m-%dT%H:%M:%S")


def datetime_to_pretty_str(date):
    """
    print a datetime in pretty formatted str format
    """
    return date.strftime("%A %d %B %Y %H:%M (UTC)")


def ISO8601_to_day_str(isodate, tz=0):
    """
    print a ISO8601 in DD/MM/YYYY formatted str
    """
    date = datetime(year=int(isodate[0:4]),
                    month=int(isodate[5:7]),
                    day=int(isodate[8:10]),
                    hour=int(isodate[11:13]),
                    minute=int(isodate[14:16]),
                    second=int(isodate[17:19]))

    if tz != 0:
        tz_i, tz_d = divmod(tz, 1)
        tz_d, _  = divmod(tz_d * 100, 1)
        date += timedelta(hours=tz_i, minutes=tz_d)

    return date.strftime("%d/%m/%Y")


def ISO8601_to_pretty_str(isodate, tz=0):
    """
    convert a ISO8601 in pretty formatted str format
    """
    if isodate is None:
        isodate = datetime_null().isoformat()

    date = datetime(year=int(isodate[0:4]),
                    month=int(isodate[5:7]),
                    day=int(isodate[8:10]),
                    hour=int(isodate[11:13]),
                    minute=int(isodate[14:16]),
                    second=int(isodate[17:19]))

    if tz != 0:
        tz_i, tz_d = divmod(tz, 1)
        tz_d, _  = divmod(tz_d * 100, 1)
        date += timedelta(hours=tz_i, minutes=tz_d)
        return date.strftime("%A %d %B %Y %H:%M")

    return datetime_to_pretty_str(date)


def asn1_datestr_to_datetime(s):
    """
    Returns a datetime for the passed asn1 formatted string
    """
    if isinstance(s, binary_type):
        s = s.decode('utf-8')

    return datetime.strptime(s[:14], "%Y%m%d%H%M%S")


def format_cert_expr_date(s):
    """
    Takes a asn1 formatted date string and tries to create an expiration date
    out of it. If that does not work, the returned expiration date is never.
    """
    try:
        return asn1_datestr_to_datetime(s)
    except:
        return datetime_never()


def iso_year_start(iso_year):
    """Returns the gregorian calendar date of the first day of the given ISO year"""
    fourth_jan = datetime.strptime('{0}-01-04'.format(iso_year), '%Y-%m-%d')
    delta = timedelta(fourth_jan.isoweekday() - 1)
    return fourth_jan - delta


def iso_to_gregorian(iso_year, iso_week, iso_day):
    """Returns gregorian calendar date for the given ISO year, week and day"""
    year_start = iso_year_start(iso_year)
    return year_start + timedelta(days=iso_day - 1, weeks=iso_week - 1)


def bytes_to_pretty_str(b):
    if isinstance(b, str):
        b = int(b)

    if b >= 1000000000:
        return "%dGB" % int(b / 1000000000)

    if b >= 1000000:
        return "%dMB" % int(b / 1000000)

    return "%dKB" % int(b / 1000)
