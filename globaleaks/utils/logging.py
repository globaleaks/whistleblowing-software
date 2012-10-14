# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import sys
from globaleaks.utils import gltime
from twisted.python import log
from twisted.python.logfile import DailyLogFile

def start():
    log.startLogging(DailyLogFile.fromFullPath('/tmp/glbackend.log'))
    log.msg("Starting GLBackend on %s (%s UTC)" %  (gltime.prettyDateNow(),
                                                    gltime.utcPrettyDateNow()))
