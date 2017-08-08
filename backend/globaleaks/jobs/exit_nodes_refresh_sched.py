# -*- coding: UTF-8
# Implement refresh of the list of exit nodes IPs.

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import LoopingJob
from globaleaks.settings import GLSettings

__all__ = ['ExitNodesRefreshSchedule']


class ExitNodesRefreshSchedule(LoopingJob):
    name = "Exit Nodes Refresh"
    interval = 3600

    def operation(self):
        # NOTE operation is intended to a be synchronous func. Here it is async
        self._operation()

    @inlineCallbacks
    def _operation(self):
        net_agent = GLSettings.get_agent()
        yield GLSettings.appstate.tor_exit_set.update(net_agent)
