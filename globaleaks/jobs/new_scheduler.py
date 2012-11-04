from twisted.internet import reactor
from apscheduler.scheduler import Scheduler




class GLSchedule(object):

    def __init__(self):

        if not self.__getattribute__('operation'):
            log.debug("Programmer: you can't use the base class GLSchedule")
            raise BaseException

    def timings(self, ):

    def operation_prologue(self, success=True):

        if success:
            reactor.callLater(self.next_exec, self.operation)
        else:
            reactor.callLater(self.next_exec_after_fail, self.operation)