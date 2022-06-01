# -*- coding: utf-8

from globaleaks.jobs.job import LoopingJob


__all__ = ['ExitNodesRefresh']


class ExitNodesRefresh(LoopingJob):
    interval=1800

    def operation(self):
        return self.state.update_tor_exits_list()
