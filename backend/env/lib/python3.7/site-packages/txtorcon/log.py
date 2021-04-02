# -*- coding: utf-8 -*-

"""
This module handles txtorcon debug messages.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from twisted.python import log as twlog

__all__ = ['txtorlog']

txtorlog = twlog.LogPublisher()


def debug_logging():
    stdobserver = twlog.PythonLoggingObserver('txtorcon')
    fileobserver = twlog.FileLogObserver(open('txtorcon.log', 'w'))

    txtorlog.addObserver(stdobserver.emit)
    txtorlog.addObserver(fileobserver.emit)
