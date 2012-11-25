# coding=utf-8
# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from storm.locals import Int, Pickle
from storm.locals import Unicode
from globaleaks.models.base import TXModel
from globaleaks.utils import log


__all__ = [ 'AdminStats', 'LocalizedTexts' ]

class AdminStats(TXModel):
    """
    every entry is the collection of the elements in the last
    node.private_stats_delta (expressed in minutes)
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminStats")
    __storm_table__ = 'adminstats'

    id = Int(primary=True)
        # XXX: perhaps related to Context.context_gus ?

    receiver_access = Int()
    download = Int()
    submission = Int()
    whistleblower_access = Int()

    download_forbidden = Int()
        # count of the download tried but deny for be expired

    access_forbidden = Int()
    removed_submission = Int()

    """
    This statistics for admininistrator, can be easily expanded, keeping track also which kind of submission
    has been forbidden, expire, created, downloaded, etc. Can be a detailed monitor of the activities.
    """

class LocalizedTexts(TXModel):
    """
    need to be defined an API, that permit the admin, to convert all the description texts and
    localize them
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class LocalizedTexts")
    __storm_table__ = 'localizedtexts'

    id = Int(primary=True)
    reference = Pickle()
    translated = Pickle()

    """
    need to be defined with the Client and in the API, but most likely would be
    a struct like the POT file, pickled in the database, and managed by administrators input
    """


