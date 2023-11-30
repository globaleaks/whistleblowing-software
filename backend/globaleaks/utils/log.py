# -*- coding: utf-8
import codecs
import glob
import gzip
import logging
import os
import sys
import traceback
from datetime import datetime

from twisted.python import log as txlog, logfile as txlogfile
from twisted.python import util, failure
from twisted.web.http import _escape


def compress_file(input_path, output_path):
    with open(input_path, 'rb') as f_in, gzip.open(output_path, 'wb') as f_out:
        f_out.writelines(f_in)


class RotatedDailyLogFile(txlogfile.DailyLogFile):
    """Extending `DailyLogFile` to serve GlobaLeaks purposes.

    Additionally to the original daily log file rotation it also allows
    call sites to control the number of rotated logfiles kept around and
    when to start compressing them.
    """
    maxRotatedFiles = 30
    compressLast = 1

    def __init__(self, name, directory, defaultMode=None,
                 maxRotatedFiles=None, compressLast=None):
        txlogfile.DailyLogFile.__init__(self, name, directory, defaultMode)
        if maxRotatedFiles is not None:
            self.maxRotatedFiles = int(maxRotatedFiles)
        if compressLast is not None:
            self.compressLast = int(compressLast)

    def shouldRotate(self):
        return True

    def _compressFile(self, path):
        """Compress the file in the given path using bzip2.

        The compressed file will be in the same path and old file
        will be removed.

        :return: the path to the compressed file.
        """
        compressed_path = '%s.gz' % path
        compress_file(path, compressed_path)
        os.remove(path)
        return compressed_path

    def rotate(self):
        """Rotate the current logfile.

        Also remove extra entries and compress the last ones.
        """
        # Rotate the log daily.
        txlogfile.DailyLogFile.rotate(self)

        # Remove 'extra' rotated log files.
        logs = self.listLogs()
        for log_path in logs[self.maxRotatedFiles:]:
            os.remove(log_path)

        # Refresh the list of existing rotated logs
        logs = self.listLogs()

        # Skip compressing if there are no files to be compressed.
        if len(logs) <= self.compressLast:
            return

        # Compress last log files.
        for log_path in logs[-self.compressLast:]:
            # Skip already compressed files.
            if log_path.endswith('gz'):
                continue
            self._compressFile(log_path)

    def listLogs(self):
        """Return the list of rotate log files, newest first."""
        return sorted(glob.glob("%s.*" % self.path), reverse=True)



def timedelta_to_milliseconds(t):
    """
    Convert a timedelta to millisecond

    :param t: the time delta object to be converted
    :return: the timedelta representation in milliseconds
    """
    return (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10**6) / 10**3.0


def log_remove_escapes(s):
    """
    This function removes escape sequence from log strings

    :param s: A string to be escaped
    :return:  The escaped string
    """
    if isinstance(s, str):
        return codecs.encode(s, 'unicode_escape').decode()
    else:
        try:
            string = str(s, 'unicode_escape')
        except UnicodeDecodeError:
            return str(s, 'string_escape')
        except Exception as e:
            return "Failure in log_remove_escapes %r" % e
        else:
            return string


def openLogFile(logfile, rotated_log_files):
    """
    Open a log file

    :param logfile: A log file path
    :param max_file_size: A maximum size accepted before rotation
    :param rotated_log_files: A number of rotated log files
    :return: A file descriptor
    """
    name = os.path.basename(logfile)
    directory = os.path.dirname(logfile)

    return RotatedDailyLogFile(name,
                               directory,
                               maxRotatedFiles=rotated_log_files)


def logFormatter(timestamp, request):
    """
    Log the request adding timestamp

    :param timestamp: A timestamp of the log entry
    :param request: A request to be logged
    :return: A formatted log entry
    """
    duration = -1

    if hasattr(request, 'start_time'):
        duration = timedelta_to_milliseconds(datetime.now() - request.start_time)

    client_ip = '[REMOVED_IP_ADDRESS]'
    client_ua = '[REMOVED_USER_AGENT]'

    if request.log_ip_and_ua:
        client_ip = request.client_ip
        client_ua = request.client_ua

    return (u'%(vhost)s %(ip)s - - %(timestamp)s "%(method)s %(uri)s %(clientproto)s" %(code)s %(length)d %(duration)dms - "%(user_agent)s"' % dict(
            vhost=_escape(request.hostname),
            timestamp=timestamp,
            duration=duration,
            ip=_escape(client_ip),
            method=_escape(request.method),
            uri=_escape(request.uri),
            clientproto=_escape(request.clientproto),
            code=request.code,
            length=request.sentLength,
            user_agent=_escape(client_ua)))


class LogObserver(txlog.FileLogObserver):
    """
    Tracks and logs exceptions generated within the application
    """

    def emit(self, eventDict):
        """
        Handles formatting system log messages along with incrementing the objs
        error counters. The eventDict is generated by the arguments passed to each
        log level call. See the unittests for an example.
        """
        if 'failure' in eventDict:
            vf = eventDict['failure']
            e_t, e_v, e_tb = vf.type, vf.value, vf.getTracebackObject()
            sys.excepthook(e_t, e_v, e_tb)

        text = txlog.textFromEventDict(eventDict)
        if text is None:
            return

        timeStr = self.formatTime(eventDict['time'])
        fmtDict = {'system': eventDict['system'], 'text': text.replace("\n", "\n\t")}
        msgStr = txlog._safeFormat("[%(system)s] %(text)s\n", fmtDict)

        util.untilConcludes(self.write, timeStr + ' ' + msgStr)
        util.untilConcludes(self.flush)


class Logger(object):
    """
    Customized LogPublisher
    """
    loglevel = logging.INFO

    _verbosity_dict = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'ERROR': logging.ERROR
    }

    def setloglevel(self, loglevel):
        self.loglevel = self._verbosity_dict[loglevel]

    def print(self, prefix, msg, *args, **kwargs):
        msg = (msg % args) if args else msg

        msg = log_remove_escapes(msg)

        tid = kwargs.get('tid', None)
        p = '[%s]' % prefix if tid is None else '[%s] [%d]' % (prefix, tid)

        print(p, msg)

    def debug(self, msg, *args, **kwargs):
        if self.loglevel and self.loglevel <= logging.DEBUG:
            self.print('D', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.loglevel and self.loglevel <= logging.INFO:
            self.print('I', msg, *args, **kwargs)

    def err(self, msg, *args, **kwargs):
        if self.loglevel:
            self.print('E', msg, *args, **kwargs)

    def exception(self, error):
        """
        Formats exceptions for output to logs and/or stdout

        :param error:
        :type error: Exception or `twisted.python.failure.Failure`
        """
        if isinstance(error, failure.Failure):
            error.printTraceback()
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)


log = Logger()
