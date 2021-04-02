# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from txtorcon._metadata import __version__, __author__, __contact__
from txtorcon._metadata import __license__, __copyright__, __url__

from txtorcon.router import Router
from txtorcon.circuit import Circuit
from txtorcon.circuit import build_timeout_circuit
from txtorcon.circuit import CircuitBuildTimedOutError
from txtorcon.stream import Stream
from txtorcon.controller import connect
from txtorcon.torcontrolprotocol import TorControlProtocol
from txtorcon.torcontrolprotocol import TorProtocolError
from txtorcon.torcontrolprotocol import TorProtocolFactory
from txtorcon.torcontrolprotocol import DEFAULT_VALUE
from txtorcon.torstate import TorState
from txtorcon.torstate import build_tor_connection
from txtorcon.torstate import build_local_tor_connection
from txtorcon.torconfig import TorConfig
from txtorcon.torconfig import HiddenService
from txtorcon.torconfig import EphemeralHiddenService
from txtorcon.torconfig import launch_tor  # this one depreceated, use launch()
from txtorcon.controller import TorProcessProtocol
from txtorcon.controller import launch  # this is "newer" one
from txtorcon.controller import Tor
from txtorcon.controller import TorNotFound
from txtorcon.torinfo import TorInfo
from txtorcon.addrmap import AddrMap
from txtorcon.endpoints import TorOnionAddress
from txtorcon.endpoints import TorOnionListeningPort
from txtorcon.endpoints import TCPHiddenServiceEndpoint
from txtorcon.endpoints import TCPHiddenServiceEndpointParser
from txtorcon.endpoints import TorClientEndpoint
from txtorcon.endpoints import TorClientEndpointStringParser
from txtorcon.endpoints import IHiddenService, IProgressProvider
from txtorcon.onion import IOnionService
from txtorcon.onion import IFilesystemOnionService
from txtorcon.onion import IAuthenticatedOnionClients
from txtorcon.onion import IOnionClient
from txtorcon.onion import FilesystemOnionService
from txtorcon.onion import FilesystemAuthenticatedOnionService
from txtorcon.onion import FilesystemAuthenticatedOnionServiceClient
from txtorcon.onion import EphemeralOnionService
from txtorcon.onion import EphemeralAuthenticatedOnionService
from txtorcon.onion import EphemeralAuthenticatedOnionServiceClient
from txtorcon.onion import AuthStealth
from txtorcon.onion import AuthBasic
from txtorcon.onion import DISCARD

from txtorcon.endpoints import get_global_tor
from . import util
from . import interface
from txtorcon.interface import (
    ITorControlProtocol,
    IStreamListener, IStreamAttacher, StreamListenerMixin,
    ICircuitContainer, ICircuitListener, CircuitListenerMixin,
    IRouterContainer, IAddrListener, ITor
)

__all__ = [
    "connect", "launch",  # connect, launch return instance of Tor()...
    "Tor", "ITor",        # ...which is the preferred high-level API
    "Router",
    "Circuit",
    "Stream",
    "TorControlProtocol", "TorProtocolError", "TorProtocolFactory",
    "TorState", "DEFAULT_VALUE",
    "TorInfo",
    "build_tor_connection", "build_local_tor_connection", "launch_tor",
    "TorNotFound", "TorConfig", "HiddenService", "EphemeralHiddenService",
    "TorProcessProtocol",
    "TorInfo",
    "TCPHiddenServiceEndpoint", "TCPHiddenServiceEndpointParser",
    "TorClientEndpoint", "TorClientEndpointStringParser",
    "IProgressProvider",
    "IHiddenService",  # deprecated
    "TorOnionAddress", "TorOnionListeningPort",

    # newest Onion API classes
    "IOnionService", "IFilesystemOnionService",
    "IAuthenticatedOnionClients", "IOnionClient",
    "AuthStealth", "AuthBasic", "DISCARD",
    # should I really export the concrete classes, too?
    "EphemeralOnionService",
    "FilesystemOnionService",
    "EphemeralAuthenticatedOnionService",
    "EphemeralAuthenticatedOnionServiceClient",
    "FilesystemAuthenticatedOnionService",
    "FilesystemAuthenticatedOnionServiceClient",

    "get_global_tor",
    "build_timeout_circuit",
    "CircuitBuildTimedOutError",

    "AddrMap",
    "util", "interface",
    "ITorControlProtocol",
    "IStreamListener", "IStreamAttacher", "StreamListenerMixin",
    "ICircuitContainer", "ICircuitListener", "CircuitListenerMixin",
    "IRouterContainer", "IAddrListener", "IProgressProvider",

    "__version__", "__author__", "__contact__",
    "__license__", "__copyright__", "__url__",
]
