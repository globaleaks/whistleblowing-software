"""
TorCtl is a python Tor controller with extensions to support path
building and various constraints on node and path selection, as well as
statistics gathering.

Apps can hook into the TorCtl package at whatever level they wish. 

The lowest level of interaction is to use the TorCtl module
(TorCtl/TorCtl.py). Typically this is done by importing TorCtl.TorCtl
and creating a TorCtl.Connection and extending from TorCtl.EventHandler.
This class receives Tor controller events packaged into python classes
from a TorCtl.Connection.

The next level up is to use the TorCtl.PathSupport module. This is done
by importing TorCtl.PathSupport and instantiating or extending from
PathSupport.PathBuilder, which itself extends from TorCtl.EventHandler.
This class handles circuit construction and stream attachment subject to
policies defined by PathSupport.NodeRestrictor and
PathSupport.PathRestrictor implementations.

If you are interested in gathering statistics, you can instead
instantiate or extend from StatsSupport.StatsHandler, which is
again an event handler with hooks to record statistics on circuit
creation, stream bandwidth, and circuit failure information.
"""

__all__ = ["TorUtil", "GeoIPSupport", "PathSupport", "TorCtl", "StatsSupport",
           "SQLSupport", "ScanSupport"]
