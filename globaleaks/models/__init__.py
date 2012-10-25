# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

"""
In here we have all of the models that create an object relational link with
their database representation.

A few things on naming convention.
__storm_table__ is the table name and it should be plural (with an s)
The name of the class starts with a capital letter and uses camel case and is
singular (no s).

The names of the modules is singular with no s
"""

__all__ = ['base', 'admin', 'receiver', 'tip', 'submission', 'node', 'context' ]

from . import base
from . import admin
from . import submission
from . import receiver
from . import tip
from . import node
from . import context


from storm.tracer import debug
import sys
# TODO: from config file enable the debug of Storm and JSON I/O of Cyclone
debug(True, sys.stdout)
