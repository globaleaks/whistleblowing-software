# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

from twisted.internet import task
from twisted.python.failure import Failure

from globaleaks.utils.utility import log
from globaleaks.utils.mailutils import mail_exception

class GLJob(task.LoopingCall):

    def __init__(self):
        task.LoopingCall.__init__(self, self._operation)

    def _operation(self):
        try:

            self.operation()

        except Exception as e:

            log.err("Exception while performin scheduled operation %s: %s" % \
                    (type(self).__name__, e))

            try:

                if isinstance(e, Failure):
                    exc_type = e.type
                    exc_value = e.value
                    exc_tb = e.getTracebackObject()
                else:
                    exc_type, exc_value, exc_tb = sys.exc_info()

                mail_exception(exc_type, exc_value, exc_tb)

            except:

                pass

    def operation(self):
        pass # dummy skel for GLJob objects
            
