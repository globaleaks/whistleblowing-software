# -*- coding: UTF-8
# 
#   models/stats
#   ************
# 
# This file contain the implementation of the statistics for GLBackend, every context
# has its own flow of stats


from storm.locals import AutoReload, Int, Unicode, DateTime, Reference
from globaleaks.models.base import TXModel
from globaleaks.utils import log
from globaleaks.models.context import Context


__all__ = [ 'Stats' ]

class Stats(TXModel):

