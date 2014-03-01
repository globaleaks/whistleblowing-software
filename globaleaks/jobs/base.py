# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

from twisted.internet import task

class GLJob(task.LoopingCall):

    def __init__(self):
        task.LoopingCall.__init__(self, self.operation)