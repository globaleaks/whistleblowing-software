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
    """
    every entry is the collection of the elements in the last
    node.private_stats_delta (expressed in minutes)

    * Follow the same logic of admin.AdminStats,
    * need to be organized along with the information that we want to shared to the WBs:
    *  active_submission represent the amount of submission active in the moment
    *  node activities is a sum of admin + receiver operation
    * that's all time dependent information
    * remind: maybe also non-time dependent information would exists, if a node want to publish also their own analyzed submission, (but this would require another db table)
    """

    __storm_table__ = 'statistics'

    id = Int(primary=True, default=AutoReload)
    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    receiver_access = Int()
    download = Int()
    submission = Int()
    whistleblower_access = Int()

    download_forbidden = Int()
    # count of the download tried but denied (due to expiration)

    access_forbidden = Int()
    removed_submission = Int()

    active_submissions = Int()
    node_activities = Int()
    uptime = Int()

