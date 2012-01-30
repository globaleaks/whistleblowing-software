#!/usr/bin/python
# TorCtl.py -- Python module to interface with Tor Control interface.
# Copyright 2005 Nick Mathewson
# Copyright 2007-2010 Mike Perry. See LICENSE file.

"""
Library to control Tor processes.

This library handles sending commands, parsing responses, and delivering
events to and from the control port. The basic usage is to create a
socket, wrap that in a TorCtl.Connection, and then add an EventHandler
to that connection. A simple example with a DebugEventHandler (that just
echoes the events back to stdout) is present in run_example().

Note that the TorCtl.Connection is fully compatible with the more
advanced EventHandlers in TorCtl.PathSupport (and of course any other
custom event handlers that you may extend off of those).

This package also contains a helper class for representing Routers, and
classes and constants for each event.
 
To quickly fetch a TorCtl instance to experiment with use the following:

>>> import TorCtl
>>> conn = TorCtl.connect()
>>> conn.get_info("version")["version"]
'0.2.1.24'

"""

__all__ = ["EVENT_TYPE", "connect", "TorCtlError", "TorCtlClosed",
           "ProtocolError", "ErrorReply", "NetworkStatus", "ExitPolicyLine",
           "Router", "RouterVersion", "Connection", "parse_ns_body",
           "EventHandler", "DebugEventHandler", "NetworkStatusEvent",
           "NewDescEvent", "CircuitEvent", "StreamEvent", "ORConnEvent",
           "StreamBwEvent", "LogEvent", "AddrMapEvent", "BWEvent",
           "BuildTimeoutSetEvent", "UnknownEvent", "ConsensusTracker",
           "EventListener", "EVENT_STATE" ]

import os
import re
import struct
import sys
import threading
import Queue
import datetime
import traceback
import socket
import getpass
import binascii
import types
import time
import copy

from TorUtil import *

if sys.version_info < (2, 5):
  from sets import Set as set
  from sha import sha as sha1
else:
  from hashlib import sha1

# Types of "EVENT" message.
EVENT_TYPE = Enum2(
          CIRC="CIRC",
          STREAM="STREAM",
          ORCONN="ORCONN",
          STREAM_BW="STREAM_BW",
          BW="BW",
          NS="NS",
          NEWCONSENSUS="NEWCONSENSUS",
          BUILDTIMEOUT_SET="BUILDTIMEOUT_SET",
          GUARD="GUARD",
          NEWDESC="NEWDESC",
          ADDRMAP="ADDRMAP",
          DEBUG="DEBUG",
          INFO="INFO",
          NOTICE="NOTICE",
          WARN="WARN",
          ERR="ERR")

EVENT_STATE = Enum2(
          PRISTINE="PRISTINE",
          PRELISTEN="PRELISTEN",
          HEARTBEAT="HEARTBEAT",
          HANDLING="HANDLING",
          POSTLISTEN="POSTLISTEN",
          DONE="DONE")

# Types of control port authentication
AUTH_TYPE = Enum2(
          NONE="NONE",
          PASSWORD="PASSWORD",
          COOKIE="COOKIE")

INCORRECT_PASSWORD_MSG = "Provided passphrase was incorrect"

def connect(controlAddr="127.0.0.1", controlPort=9051, passphrase=None):
  """
  Convenience function for quickly getting a TorCtl connection. This is very
  handy for debugging or CLI setup, handling setup and prompting for a password
  if necessary (if either none is provided as input or it fails). If any issues
  arise this prints a description of the problem and returns None.
  
  Arguments:
    controlAddr - ip address belonging to the controller
    controlPort - port belonging to the controller
    passphrase  - authentication passphrase (if defined this is used rather
                  than prompting the user)
  """
  
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((controlAddr, controlPort))
    conn = Connection(s)
    authType, authValue = conn.get_auth_type(), ""
    
    if authType == AUTH_TYPE.PASSWORD:
      # password authentication, promting for the password if it wasn't provided
      if passphrase: authValue = passphrase
      else:
        try: authValue = getpass.getpass()
        except KeyboardInterrupt: return None
    elif authType == AUTH_TYPE.COOKIE:
      authValue = conn.get_auth_cookie_path()
    
    conn.authenticate(authValue)
    return conn
  except socket.error, exc:
    if "Connection refused" in exc.args:
      # most common case - tor control port isn't available
      print "Connection refused. Is the ControlPort enabled?"
    else: print "Failed to establish socket: %s" % exc
    
    return None
  except Exception, exc:
    if passphrase and str(exc) == "Unable to authenticate: password incorrect":
      # provide a warning that the provided password didn't work, then try
      # again prompting for the user to enter it
      print INCORRECT_PASSWORD_MSG
      return connect(controlAddr, controlPort)
    else:
      print exc
      return None

class TorCtlError(Exception):
  "Generic error raised by TorControl code."
  pass

class TorCtlClosed(TorCtlError):
  "Raised when the controller connection is closed by Tor (not by us.)"
  pass

class ProtocolError(TorCtlError):
  "Raised on violations in Tor controller protocol"
  pass

class ErrorReply(TorCtlError):
  "Raised when Tor controller returns an error"
  def __init__(self, *args, **kwargs):
    if "status" in kwargs:
      self.status = kwargs.pop("status")
    if "message" in kwargs:
      self.message = kwargs.pop("message")
    TorCtlError.__init__(self, *args, **kwargs)

class NetworkStatus:
  "Filled in during NS events"
  def __init__(self, nickname, idhash, orhash, updated, ip, orport, dirport, flags, bandwidth=None):
    self.nickname = nickname
    self.idhash = idhash
    self.orhash = orhash
    self.ip = ip
    self.orport = int(orport)
    self.dirport = int(dirport)
    self.flags = flags
    self.idhex = (self.idhash + "=").decode("base64").encode("hex").upper()
    self.bandwidth = bandwidth
    m = re.search(r"(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)", updated)
    self.updated = datetime.datetime(*map(int, m.groups()))

class Event:
  def __init__(self, event_name):
    self.event_name = event_name
    self.arrived_at = 0
    self.state = EVENT_STATE.PRISTINE

class TimerEvent(Event):
  def __init__(self, event_name, type):
    Event.__init__(self, event_name)
    self.type = type

class NetworkStatusEvent(Event):
  def __init__(self, event_name, nslist):
    Event.__init__(self, event_name)
    self.nslist = nslist # List of NetworkStatus objects

class NewConsensusEvent(NetworkStatusEvent):
  pass

class NewDescEvent(Event):
  def __init__(self, event_name, idlist):
    Event.__init__(self, event_name)
    self.idlist = idlist

class GuardEvent(Event):
  def __init__(self, event_name, ev_type, guard, status):
    Event.__init__(self, event_name)
    if "~" in guard:
      (self.idhex, self.nick) = guard[1:].split("~")
    elif "=" in guard:
      (self.idhex, self.nick) = guard[1:].split("=")
    else:
      self.idhex = guard[1:]
    self.status = status

class BuildTimeoutSetEvent(Event):
  def __init__(self, event_name, set_type, total_times, timeout_ms, xm, alpha,
               quantile):
    Event.__init__(self, event_name)
    self.set_type = set_type
    self.total_times = total_times
    self.timeout_ms = timeout_ms
    self.xm = xm
    self.alpha = alpha
    self.cutoff_quantile = quantile

class CircuitEvent(Event):
  def __init__(self, event_name, circ_id, status, path, purpose,
         reason, remote_reason):
    Event.__init__(self, event_name)
    self.circ_id = circ_id
    self.status = status
    self.path = path
    self.purpose = purpose
    self.reason = reason
    self.remote_reason = remote_reason

class StreamEvent(Event):
  def __init__(self, event_name, strm_id, status, circ_id, target_host,
         target_port, reason, remote_reason, source, source_addr, purpose):
    Event.__init__(self, event_name)
    self.strm_id = strm_id
    self.status = status
    self.circ_id = circ_id
    self.target_host = target_host
    self.target_port = int(target_port)
    self.reason = reason
    self.remote_reason = remote_reason
    self.source = source
    self.source_addr = source_addr
    self.purpose = purpose

class ORConnEvent(Event):
  def __init__(self, event_name, status, endpoint, age, read_bytes,
         wrote_bytes, reason, ncircs):
    Event.__init__(self, event_name)
    self.status = status
    self.endpoint = endpoint
    self.age = age
    self.read_bytes = read_bytes
    self.wrote_bytes = wrote_bytes
    self.reason = reason
    self.ncircs = ncircs

class StreamBwEvent(Event):
  def __init__(self, event_name, strm_id, written, read):
    Event.__init__(self, event_name)
    self.strm_id = int(strm_id)
    self.bytes_read = int(read)
    self.bytes_written = int(written)

class LogEvent(Event):
  def __init__(self, level, msg):
    Event.__init__(self, level)
    self.level = level
    self.msg = msg

class AddrMapEvent(Event):
  def __init__(self, event_name, from_addr, to_addr, when):
    Event.__init__(self, event_name)
    self.from_addr = from_addr
    self.to_addr = to_addr
    self.when = when

class AddrMap:
  def __init__(self, from_addr, to_addr, when):
    self.from_addr = from_addr
    self.to_addr = to_addr
    self.when = when

class BWEvent(Event):
  def __init__(self, event_name, read, written):
    Event.__init__(self, event_name)
    self.read = read
    self.written = written

class UnknownEvent(Event):
  def __init__(self, event_name, event_string):
    Event.__init__(self, event_name)
    self.event_string = event_string

ipaddress_re = re.compile(r"(\d{1,3}\.){3}\d{1,3}$")
class ExitPolicyLine:
  """ Class to represent a line in a Router's exit policy in a way 
      that can be easily checked. """
  def __init__(self, match, ip_mask, port_low, port_high):
    self.match = match
    if ip_mask == "*":
      self.ip = 0
      self.netmask = 0
    else:
      if not "/" in ip_mask:
        self.netmask = 0xFFFFFFFF
        ip = ip_mask
      else:
        ip, mask = ip_mask.split("/")
        if ipaddress_re.match(mask):
          self.netmask=struct.unpack(">I", socket.inet_aton(mask))[0]
        else:
          self.netmask = 0xffffffff ^ (0xffffffff >> int(mask))
      self.ip = struct.unpack(">I", socket.inet_aton(ip))[0]
    self.ip &= self.netmask
    if port_low == "*":
      self.port_low,self.port_high = (0,65535)
    else:
      if not port_high:
        port_high = port_low
      self.port_low = int(port_low)
      self.port_high = int(port_high)
  
  def check(self, ip, port):
    """Check to see if an ip and port is matched by this line. 
     Returns true if the line is an Accept, and False if it is a Reject. """
    ip = struct.unpack(">I", socket.inet_aton(ip))[0]
    if (ip & self.netmask) == self.ip:
      if self.port_low <= port and port <= self.port_high:
        return self.match
    return -1

  def __str__(self):
    retr = ""
    if self.match:
      retr += "accept "
    else:
      retr += "reject "
    retr += socket.inet_ntoa(struct.pack(">I",self.ip)) + "/"
    retr += socket.inet_ntoa(struct.pack(">I",self.netmask)) + ":"
    retr += str(self.port_low)+"-"+str(self.port_high)
    return retr

class RouterVersion:
  """ Represents a Router's version. Overloads all comparison operators
      to check for newer, older, or equivalent versions. """
  def __init__(self, version):
    if version:
      v = re.search("^(\d+)\.(\d+)\.(\d+)\.(\d+)", version).groups()
      self.version = int(v[0])*0x1000000 + int(v[1])*0x10000 + int(v[2])*0x100 + int(v[3])
      self.ver_string = version
    else: 
      self.version = version
      self.ver_string = "unknown"

  def __lt__(self, other): return self.version < other.version
  def __gt__(self, other): return self.version > other.version
  def __ge__(self, other): return self.version >= other.version
  def __le__(self, other): return self.version <= other.version
  def __eq__(self, other): return self.version == other.version
  def __ne__(self, other): return self.version != other.version
  def __str__(self): return self.ver_string


# map descriptor keywords to regular expressions.
desc_re = {
  "router":          r"(\S+) (\S+)",
  "opt fingerprint": r"(.+).*on (\S+)",
  "opt extra-info-digest": r"(\S+)",
  "opt hibernating": r"1$",
  "platform":  r"Tor (\S+).*on ([\S\s]+)",
  "accept":    r"(\S+):([^-]+)(?:-(\d+))?",
  "reject":    r"(\S+):([^-]+)(?:-(\d+))?",
  "bandwidth": r"(\d+) \d+ (\d+)",
  "uptime":    r"(\d+)",
  "contact":   r"(.+)",
  "published": r"(\S+ \S+)",
}
# Compile each regular expression now.
for kw, reg in desc_re.iteritems():
  desc_re[kw] = re.compile(reg)

def partition(string, delimiter):
  """ Implementation of string.partition-like function for Python <
  2.5.  Returns a tuple (first, rest), where first is the text up to
  the first delimiter, and rest is the text after the first delimiter.
  """
  sp = string.split(delimiter, 1)
  if len(sp) > 1:
    return sp[0], sp[1]
  else:
    return sp[0], ""

class Router:
  """ 
  Class to represent a router from a descriptor. Can either be
  created from the parsed fields, or can be built from a
  descriptor+NetworkStatus 
  """     
  def __init__(self, *args):
    if len(args) == 1:
      for i in args[0].__dict__:
        self.__dict__[i] =  copy.deepcopy(args[0].__dict__[i])
      return
    else:
      (idhex, name, bw, down, exitpolicy, flags, ip, version, os, uptime,
       published, contact, rate_limited, orhash,
       ns_bandwidth,extra_info_digest) = args
    self.idhex = idhex
    self.nickname = name
    if ns_bandwidth != None:
      self.bw = ns_bandwidth
    else:
     self.bw = bw
    self.desc_bw = bw
    self.exitpolicy = exitpolicy
    self.flags = flags # Technicaly from NS doc
    self.down = down
    self.ip = struct.unpack(">I", socket.inet_aton(ip))[0]
    self.version = RouterVersion(version)
    self.os = os
    self.list_rank = 0 # position in a sorted list of routers.
    self.uptime = uptime
    self.published = published
    self.refcount = 0 # How many open circs are we currently in?
    self.deleted = False # Has Tor already deleted this descriptor?
    self.contact = contact
    self.rate_limited = rate_limited
    self.orhash = orhash
    self.extra_info_digest = extra_info_digest
    self._generated = [] # For ExactUniformGenerator

  def __str__(self):
    s = self.idhex, self.nickname
    return s.__str__()

  def build_from_desc(desc, ns):
    """
    Static method of Router that parses a descriptor string into this class.
    'desc' is a full descriptor as a string. 
    'ns' is a TorCtl.NetworkStatus instance for this router (needed for
    the flags, the nickname, and the idhex string). 
    Returns a Router instance.
    """
    exitpolicy = []
    dead = not ("Running" in ns.flags)
    bw_observed = 0
    version = None
    os = None
    uptime = 0
    ip = 0
    router = "[none]"
    published = "never"
    contact = None
    extra_info_digest = None

    for line in desc:
      # Pull off the keyword...
      kw, rest = partition(line, " ")

      # ...and if it's "opt", extend it by the next keyword
      # so we get "opt hibernating" as one keyword.
      if kw == "opt":
        okw, rest = partition(rest, " ")
        kw += " " + okw

      # try to match the descriptor line by keyword.
      try:
        match = desc_re[kw].match(rest)
      # if we don't handle this keyword, just move on to the next one.
      except KeyError:
        continue
      # if we do handle this keyword but its data is malformed,
      # move on to the next one without processing it.
      if not match:
        continue

      g = match.groups()

      # Handle each keyword individually.
      # TODO: This could possibly be sped up since we technically already
      # did the compare with the dictionary lookup... lambda magic time.
      if kw == "accept":
        exitpolicy.append(ExitPolicyLine(True, *g))
      elif kw == "reject":
        exitpolicy.append(ExitPolicyLine(False, *g))
      elif kw == "router":
        router,ip = g
      elif kw == "bandwidth":
        bws = map(int, g)
        bw_observed = min(bws)
        rate_limited = False
        if bws[0] < bws[1]:
          rate_limited = True
      elif kw == "platform":
        version, os = g
      elif kw == "uptime":
        uptime = int(g[0])
      elif kw == "published":
        t = time.strptime(g[0] + " UTC", "20%y-%m-%d %H:%M:%S %Z")
        published = datetime.datetime(*t[0:6])
      elif kw == "contact":
        contact = g[0]
      elif kw == "opt extra-info-digest":
        extra_info_digest = g[0]
      elif kw == "opt hibernating":
        dead = True 
        if ("Running" in ns.flags):
          plog("INFO", "Hibernating router "+ns.nickname+" is running, flags: "+" ".join(ns.flags))

    if router != ns.nickname:
      plog("INFO", "Got different names " + ns.nickname + " vs " +
             router + " for " + ns.idhex)
    if not bw_observed and not dead and ("Valid" in ns.flags):
      plog("INFO", "No bandwidth for live router "+ns.nickname+", flags: "+" ".join(ns.flags))
      dead = True
    if not version or not os:
      plog("INFO", "No version and/or OS for router " + ns.nickname)
    return Router(ns.idhex, ns.nickname, bw_observed, dead, exitpolicy,
        ns.flags, ip, version, os, uptime, published, contact, rate_limited,
        ns.orhash, ns.bandwidth, extra_info_digest)
  build_from_desc = Callable(build_from_desc)

  def update_to(self, new):
    """ Somewhat hackish method to update this router to be a copy of
    'new' """
    if self.idhex != new.idhex:
      plog("ERROR", "Update of router "+self.nickname+"changes idhex!")
    for i in new.__dict__.iterkeys():
      if i == "refcount" or i == "_generated": continue
      self.__dict__[i] = new.__dict__[i]

  def will_exit_to(self, ip, port):
    """ Check the entire exitpolicy to see if the router will allow
        connections to 'ip':'port' """
    for line in self.exitpolicy:
      ret = line.check(ip, port)
      if ret != -1:
        return ret
    plog("WARN", "No matching exit line for "+self.nickname)
    return False
   
class Connection:
  """A Connection represents a connection to the Tor process via the 
     control port."""
  def __init__(self, sock):
    """Create a Connection to communicate with the Tor process over the
       socket 'sock'.
    """
    self._handler = None
    self._handleFn = None
    self._sendLock = threading.RLock()
    self._queue = Queue.Queue()
    self._thread = None
    self._closedEx = None
    self._closed = 0
    self._closeHandler = None
    self._eventThread = None
    self._eventQueue = Queue.Queue()
    self._s = BufSock(sock)
    self._debugFile = None
    
    # authentication information (lazily fetched so None if still unknown)
    self._authType = None
    self._cookiePath = None

  def get_auth_type(self):
    """
    Provides the authentication type used for the control port (a member of
    the AUTH_TYPE enumeration). This raises an IOError if this fails to query
    the PROTOCOLINFO.
    """
    
    if self._authType: return self._authType
    else:
      # check PROTOCOLINFO for authentication type
      try:
        authInfo = self.sendAndRecv("PROTOCOLINFO\r\n")[1][1]
      except ErrorReply, exc:
        raise IOError("Unable to query PROTOCOLINFO for the authentication type: %s" % exc)
      
      authType, cookiePath = None, None
      if authInfo.startswith("AUTH METHODS=NULL"):
        # no authentication required
        authType = AUTH_TYPE.NONE
      elif authInfo.startswith("AUTH METHODS=HASHEDPASSWORD"):
        # password authentication
        authType = AUTH_TYPE.PASSWORD
      elif authInfo.startswith("AUTH METHODS=COOKIE"):
        # cookie authentication, parses authentication cookie path
        authType = AUTH_TYPE.COOKIE
        
        start = authInfo.find("COOKIEFILE=\"") + 12
        end = authInfo.find("\"", start)
        cookiePath = authInfo[start:end]
      else:
        # not of a recognized authentication type (new addition to the
        # control-spec?)
        raise IOError("Unrecognized authentication type: %s" % authInfo)
      
      self._authType = authType
      self._cookiePath = cookiePath
      return self._authType
  
  def get_auth_cookie_path(self):
    """
    Provides the path of tor's authentication cookie. If the connection isn't
    using cookie authentication then this provides None. This raises an IOError
    if PROTOCOLINFO can't be queried.
    """
    
    # fetches authentication type and cookie path if still unloaded
    if self._authType == None: self.get_auth_type()
    
    if self._authType == AUTH_TYPE.COOKIE:
      return self._cookiePath
    else:
      return None
  
  def set_close_handler(self, handler):
    """Call 'handler' when the Tor process has closed its connection or
       given us an exception.  If we close normally, no arguments are
       provided; otherwise, it will be called with an exception as its
       argument.
    """
    self._closeHandler = handler

  def close(self):
    """Shut down this controller connection"""
    self._sendLock.acquire()
    try:
      self._queue.put("CLOSE")
      self._eventQueue.put((time.time(), "CLOSE"))
      self._closed = 1
      # XXX: For some reason, this does not cause the readline in
      # self._read_reply() to return immediately. The _loop() thread
      # thus tends to stick around until some event causes data to come
      # back...
      self._s.close()
      self._eventThread.join()
    finally:
      self._sendLock.release()

  def is_live(self):
    """ Returns true iff the connection is alive and healthy"""
    return self._thread.isAlive() and self._eventThread.isAlive() and not \
           self._closed

  def launch_thread(self, daemon=1):
    """Launch a background thread to handle messages from the Tor process."""
    assert self._thread is None
    t = threading.Thread(target=self._loop, name="TorLoop")
    if daemon:
      t.setDaemon(daemon)
    t.start()
    self._thread = t
    t = threading.Thread(target=self._eventLoop, name="EventLoop")
    if daemon:
      t.setDaemon(daemon)
    t.start()
    self._eventThread = t
    # eventThread provides a more reliable indication of when we are done.
    # The _loop thread won't always die when self.close() is called.
    return self._eventThread

  def _loop(self):
    """Main subthread loop: Read commands from Tor, and handle them either
       as events or as responses to other commands.
    """
    while 1:
      try:
        isEvent, reply = self._read_reply()
      except TorCtlClosed:
        plog("NOTICE", "Tor closed control connection. Exiting event thread.")
        return
      except Exception,e:
        if not self._closed:
          if sys:
            self._err(sys.exc_info())
          else:
            plog("NOTICE", "No sys left at exception shutdown: "+str(e))
            self._err((e.__class__, e, None))
          return
        else:
          isEvent = 0

      if isEvent:
        if self._handler is not None:
          self._eventQueue.put((time.time(), reply))
      else:
        cb = self._queue.get() # atomic..
        if cb == "CLOSE":
          self._s = None
          plog("INFO", "Closed control connection. Exiting thread.")
          return
        else:
          cb(reply)

  def _err(self, (tp, ex, tb), fromEventLoop=0):
    """DOCDOC"""
    # silent death is bad :(
    traceback.print_exception(tp, ex, tb)
    if self._s:
      try:
        self.close()
      except:
        pass
    self._sendLock.acquire()
    try:
      self._closedEx = ex
      self._closed = 1
    finally:
      self._sendLock.release()
    while 1:
      try:
        cb = self._queue.get(timeout=0)
        if cb != "CLOSE":
          cb("EXCEPTION")
      except Queue.Empty:
        break
    if self._closeHandler is not None:
      self._closeHandler(ex)
    # I hate you for making me resort to this, python
    os.kill(os.getpid(), 15)
    return

  def _eventLoop(self):
    """DOCDOC"""
    while 1:
      (timestamp, reply) = self._eventQueue.get()
      if reply[0][0] == "650" and reply[0][1] == "OK":
        plog("DEBUG", "Ignoring incompatible syntactic sugar: 650 OK")
        continue
      if reply == "CLOSE":
        plog("INFO", "Event loop received close message.")
        return
      try:
        self._handleFn(timestamp, reply)
      except:
        for code, msg, data in reply:
            plog("WARN", "No event for: "+str(code)+" "+str(msg))
        self._err(sys.exc_info(), 1)
        return

  def _sendImpl(self, sendFn, msg):
    """DOCDOC"""
    if self._thread is None and not self._closed:
      self.launch_thread(1)
    # This condition will get notified when we've got a result...
    condition = threading.Condition()
    # Here's where the result goes...
    result = []

    if self._closedEx is not None:
      raise self._closedEx
    elif self._closed:
      raise TorCtlClosed()

    def cb(reply,condition=condition,result=result):
      condition.acquire()
      try:
        result.append(reply)
        condition.notify()
      finally:
        condition.release()

    # Sends a message to Tor...
    self._sendLock.acquire() # ensure queue+sendmsg is atomic
    try:
      self._queue.put(cb)
      sendFn(msg) # _doSend(msg)
    finally:
      self._sendLock.release()

    # Now wait till the answer is in...
    condition.acquire()
    try:
      while not result:
        condition.wait()
    finally:
      condition.release()

    # ...And handle the answer appropriately.
    assert len(result) == 1
    reply = result[0]
    if reply == "EXCEPTION":
      raise self._closedEx

    return reply


  def debug(self, f):
    """DOCDOC"""
    self._debugFile = f

  def set_event_handler(self, handler):
    """Cause future events from the Tor process to be sent to 'handler'.
    """
    if self._handler:
      handler.pre_listeners = self._handler.pre_listeners
      handler.post_listeners = self._handler.post_listeners
    self._handler = handler
    self._handler.c = self
    self._handleFn = handler._handle1

  def add_event_listener(self, listener):
    if not self._handler:
      self.set_event_handler(EventHandler())
    self._handler.add_event_listener(listener)

  def block_until_close(self):
    """ Blocks until the connection to the Tor process is interrupted"""
    return self._eventThread.join()

  def _read_reply(self):
    lines = []
    while 1:
      line = self._s.readline()
      if not line:
        self._closed = True
        raise TorCtlClosed() 
      line = line.strip()
      if self._debugFile:
        self._debugFile.write(str(time.time())+"\t  %s\n" % line)
      if len(line)<4:
        raise ProtocolError("Badly formatted reply line: Too short")
      code = line[:3]
      tp = line[3]
      s = line[4:]
      if tp == "-":
        lines.append((code, s, None))
      elif tp == " ":
        lines.append((code, s, None))
        isEvent = (lines and lines[0][0][0] == '6')
        return isEvent, lines
      elif tp != "+":
        raise ProtocolError("Badly formatted reply line: unknown type %r"%tp)
      else:
        more = []
        while 1:
          line = self._s.readline()
          if self._debugFile:
            self._debugFile.write("+++ %s" % line)
          if line in (".\r\n", ".\n", "650 OK\n", "650 OK\r\n"): 
            break
          more.append(line)
        lines.append((code, s, unescape_dots("".join(more))))
        isEvent = (lines and lines[0][0][0] == '6')
        if isEvent: # Need "250 OK" if it's not an event. Otherwise, end
          return (isEvent, lines)

    # Notreached
    raise TorCtlError()

  def _doSend(self, msg):
    if self._debugFile:
      amsg = msg
      lines = amsg.split("\n")
      if len(lines) > 2:
        amsg = "\n".join(lines[:2]) + "\n"
      self._debugFile.write(str(time.time())+"\t>>> "+amsg)
    self._s.write(msg)

  def set_timer(self, in_seconds, type=None):
    event = (("650", "TORCTL_TIMER", type),)
    threading.Timer(in_seconds, lambda: 
                  self._eventQueue.put((time.time(), event))).start()

  def set_periodic_timer(self, every_seconds, type=None):
    event = (("650", "TORCTL_TIMER", type),)
    def notlambda():
      plog("DEBUG", "Timer fired for type "+str(type))
      self._eventQueue.put((time.time(), event))
      self._eventQueue.put((time.time(), event))
      threading.Timer(every_seconds, notlambda).start()
    threading.Timer(every_seconds, notlambda).start()

  def sendAndRecv(self, msg="", expectedTypes=("250", "251")):
    """Helper: Send a command 'msg' to Tor, and wait for a command
       in response.  If the response type is in expectedTypes,
       return a list of (tp,body,extra) tuples.  If it is an
       error, raise ErrorReply.  Otherwise, raise ProtocolError.
    """
    if type(msg) == types.ListType:
      msg = "".join(msg)
    assert msg.endswith("\r\n")

    lines = self._sendImpl(self._doSend, msg)

    # print lines
    for tp, msg, _ in lines:
      if tp[0] in '45':
        code = int(tp[:3])
        raise ErrorReply("%s %s"%(tp, msg), status = code, message = msg)
      if tp not in expectedTypes:
        raise ProtocolError("Unexpectd message type %r"%tp)

    return lines

  def authenticate(self, secret=""):
    """
    Authenticates to the control port. If an issue arises this raises either of
    the following:
      - IOError for failures in reading an authentication cookie or querying
        PROTOCOLINFO.
      - TorCtl.ErrorReply for authentication failures or if the secret is
        undefined when using password authentication
    """
    
    # fetches authentication type and cookie path if still unloaded
    if self._authType == None: self.get_auth_type()
    
    # validates input
    if self._authType == AUTH_TYPE.PASSWORD and secret == "":
      raise ErrorReply("Unable to authenticate: no passphrase provided")
    
    authCookie = None
    try:
      if self._authType == AUTH_TYPE.NONE:
        self.authenticate_password("")
      elif self._authType == AUTH_TYPE.PASSWORD:
        self.authenticate_password(secret)
      else:
        authCookie = open(self._cookiePath, "r")
        self.authenticate_cookie(authCookie)
        authCookie.close()
    except ErrorReply, exc:
      if authCookie: authCookie.close()
      issue = str(exc)
      
      # simplifies message if the wrong credentials were provided (common
      # mistake)
      if issue.startswith("515 Authentication failed: "):
        if issue[27:].startswith("Password did not match"):
          issue = "password incorrect"
        elif issue[27:] == "Wrong length on authentication cookie.":
          issue = "cookie value incorrect"
      
      raise ErrorReply("Unable to authenticate: %s" % issue)
    except IOError, exc:
      if authCookie: authCookie.close()
      issue = None
      
      # cleaner message for common errors
      if str(exc).startswith("[Errno 13] Permission denied"):
        issue = "permission denied"
      elif str(exc).startswith("[Errno 2] No such file or directory"):
        issue = "file doesn't exist"
      
      # if problem's recognized give concise message, otherwise print exception
      # string
      if issue: raise IOError("Failed to read authentication cookie (%s): %s" % (issue, self._cookiePath))
      else: raise IOError("Failed to read authentication cookie: %s" % exc)
  
  def authenticate_password(self, secret=""):
    """Sends an authenticating secret (password) to Tor.  You'll need to call 
       this method (or authenticate_cookie) before Tor can start.
    """
    #hexstr = binascii.b2a_hex(secret)
    self.sendAndRecv("AUTHENTICATE \"%s\"\r\n"%secret)
  
  def authenticate_cookie(self, cookie):
    """Sends an authentication cookie to Tor. This may either be a file or 
       its contents.
    """
    
    # read contents if provided a file
    if type(cookie) == file: cookie = cookie.read()
    
    # unlike passwords the cookie contents isn't enclosed by quotes
    self.sendAndRecv("AUTHENTICATE %s\r\n" % binascii.b2a_hex(cookie))

  def get_option(self, name):
    """Get the value of the configuration option named 'name'.  To
       retrieve multiple values, pass a list for 'name' instead of
       a string.  Returns a list of (key,value) pairs.
       Refer to section 3.3 of control-spec.txt for a list of valid names.
    """
    if not isinstance(name, str):
      name = " ".join(name)
    lines = self.sendAndRecv("GETCONF %s\r\n" % name)

    r = []
    for _,line,_ in lines:
      try:
        key, val = line.split("=", 1)
        r.append((key,val))
      except ValueError:
        r.append((line, None))

    return r

  def set_option(self, key, value):
    """Set the value of the configuration option 'key' to the value 'value'.
    """
    self.set_options([(key, value)])

  def set_options(self, kvlist):
    """Given a list of (key,value) pairs, set them as configuration
       options.
    """
    if not kvlist:
      return
    msg = " ".join(["%s=\"%s\""%(k,quote(v)) for k,v in kvlist])
    self.sendAndRecv("SETCONF %s\r\n"%msg)

  def reset_options(self, keylist):
    """Reset the options listed in 'keylist' to their default values.

       Tor started implementing this command in version 0.1.1.7-alpha;
       previous versions wanted you to set configuration keys to "".
       That no longer works.
    """
    self.sendAndRecv("RESETCONF %s\r\n"%(" ".join(keylist)))

  def get_consensus(self):
    """Get the pristine Tor Consensus. Returns a list of
       TorCtl.NetworkStatus instances."""
    return parse_ns_body(self.sendAndRecv("GETINFO dir/status-vote/current/consensus\r\n")[0][2])

  def get_network_status(self, who="all"):
    """Get the entire network status list. Returns a list of
       TorCtl.NetworkStatus instances."""
    return parse_ns_body(self.sendAndRecv("GETINFO ns/"+who+"\r\n")[0][2])

  def get_address_mappings(self, type="all"):
    # TODO: Also parse errors and GMTExpiry
    body = self.sendAndRecv("GETINFO address-mappings/"+type+"\r\n")
      
    #print "|"+body[0][1].replace("address-mappings/"+type+"=", "")+"|"
    #print str(body[0])

    if body[0][1].replace("address-mappings/"+type+"=", "") != "":
      # one line
      lines = [body[0][1].replace("address-mappings/"+type+"=", "")]
    elif not body[0][2]:
      return []
    else:
      lines = body[0][2].split("\n")
    if not lines: return []
    ret = []
    for l in lines:
      #print "|"+str(l)+"|"
      if len(l) == 0: continue #Skip last line.. it's empty
      m = re.match(r'(\S+)\s+(\S+)\s+(\"[^"]+\"|\w+)', l)
      if not m:
        raise ProtocolError("ADDRMAP response misformatted.")
      fromaddr, toaddr, when = m.groups()
      if when.upper() == "NEVER":  
        when = None
      else:
        when = time.strptime(when[1:-1], "%Y-%m-%d %H:%M:%S")
      ret.append(AddrMap(fromaddr, toaddr, when))
    return ret

  def get_router(self, ns):
    """Fill in a Router class corresponding to a given NS class"""
    desc = self.sendAndRecv("GETINFO desc/id/" + ns.idhex + "\r\n")[0][2]
    sig_start = desc.find("\nrouter-signature\n")+len("\nrouter-signature\n")
    fp_base64 = sha1(desc[:sig_start]).digest().encode("base64")[:-2]
    r = Router.build_from_desc(desc.split("\n"), ns)
    if fp_base64 != ns.orhash:
      plog("INFO", "Router descriptor for "+ns.idhex+" does not match ns fingerprint (NS @ "+str(ns.updated)+" vs Desc @ "+str(r.published)+")")
      return None
    else:
      return r


  def read_routers(self, nslist):
    """ Given a list a NetworkStatuses in 'nslist', this function will 
        return a list of new Router instances.
    """
    bad_key = 0
    new = []
    for ns in nslist:
      try:
        r = self.get_router(ns)
        if r:
          new.append(r)
      except ErrorReply:
        bad_key += 1
        if "Running" in ns.flags:
          plog("NOTICE", "Running router "+ns.nickname+"="
             +ns.idhex+" has no descriptor")
  
    return new

  def get_info(self, name):
    """Return the value of the internal information field named 'name'.
       Refer to section 3.9 of control-spec.txt for a list of valid names.
       DOCDOC
    """
    if not isinstance(name, str):
      name = " ".join(name)
    lines = self.sendAndRecv("GETINFO %s\r\n"%name)
    d = {}
    for _,msg,more in lines:
      if msg == "OK":
        break
      try:
        k,rest = msg.split("=",1)
      except ValueError:
        raise ProtocolError("Bad info line %r",msg)
      if more:
        d[k] = more
      else:
        d[k] = rest
    return d

  def set_events(self, events, extended=False):
    """Change the list of events that the event handler is interested
       in to those in 'events', which is a list of event names.
       Recognized event names are listed in section 3.3 of the control-spec
    """
    if extended:
      plog ("DEBUG", "SETEVENTS EXTENDED %s\r\n" % " ".join(events))
      self.sendAndRecv("SETEVENTS EXTENDED %s\r\n" % " ".join(events))
    else:
      self.sendAndRecv("SETEVENTS %s\r\n" % " ".join(events))

  def save_conf(self):
    """Flush all configuration changes to disk.
    """
    self.sendAndRecv("SAVECONF\r\n")

  def send_signal(self, sig):
    """Send the signal 'sig' to the Tor process; The allowed values for
       'sig' are listed in section 3.6 of control-spec.
    """
    sig = { 0x01 : "HUP",
        0x02 : "INT",
        0x03 : "NEWNYM",
        0x0A : "USR1",
        0x0C : "USR2",
        0x0F : "TERM" }.get(sig,sig)
    self.sendAndRecv("SIGNAL %s\r\n"%sig)

  def resolve(self, host):
    """ Launch a remote hostname lookup request:
        'host' may be a hostname or IPv4 address
    """
    # TODO: handle "mode=reverse"
    self.sendAndRecv("RESOLVE %s\r\n"%host)

  def map_address(self, kvList):
    """ Sends the MAPADDRESS command for each of the tuples in kvList """
    if not kvList:
      return
    m = " ".join([ "%s=%s" for k,v in kvList])
    lines = self.sendAndRecv("MAPADDRESS %s\r\n"%m)
    r = []
    for _,line,_ in lines:
      try:
        key, val = line.split("=", 1)
      except ValueError:
        raise ProtocolError("Bad address line %r",v)
      r.append((key,val))
    return r

  def extend_circuit(self, circid=None, hops=None):
    """Tell Tor to extend the circuit identified by 'circid' through the
       servers named in the list 'hops'.
    """
    if circid is None:
      circid = 0
    if hops is None:
      hops = ""
    plog("DEBUG", "Extending circuit")
    lines = self.sendAndRecv("EXTENDCIRCUIT %d %s\r\n"
                  %(circid, ",".join(hops)))
    tp,msg,_ = lines[0]
    m = re.match(r'EXTENDED (\S*)', msg)
    if not m:
      raise ProtocolError("Bad extended line %r",msg)
    plog("DEBUG", "Circuit extended")
    return int(m.group(1))

  def redirect_stream(self, streamid, newaddr, newport=""):
    """DOCDOC"""
    if newport:
      self.sendAndRecv("REDIRECTSTREAM %d %s %s\r\n"%(streamid, newaddr, newport))
    else:
      self.sendAndRecv("REDIRECTSTREAM %d %s\r\n"%(streamid, newaddr))

  def attach_stream(self, streamid, circid, hop=None):
    """Attach a stream to a circuit, specify both by IDs. If hop is given, 
       try to use the specified hop in the circuit as the exit node for 
       this stream.
    """
    if hop:
      self.sendAndRecv("ATTACHSTREAM %d %d HOP=%d\r\n"%(streamid, circid, hop))
      plog("DEBUG", "Attaching stream: "+str(streamid)+" to hop "+str(hop)+" of circuit "+str(circid))
    else:
      self.sendAndRecv("ATTACHSTREAM %d %d\r\n"%(streamid, circid))
      plog("DEBUG", "Attaching stream: "+str(streamid)+" to circuit "+str(circid))

  def close_stream(self, streamid, reason=0, flags=()):
    """DOCDOC"""
    self.sendAndRecv("CLOSESTREAM %d %s %s\r\n"
              %(streamid, reason, "".join(flags)))

  def close_circuit(self, circid, reason=0, flags=()):
    """DOCDOC"""
    self.sendAndRecv("CLOSECIRCUIT %d %s %s\r\n"
              %(circid, reason, "".join(flags)))

  def post_descriptor(self, desc):
    self.sendAndRecv("+POSTDESCRIPTOR purpose=controller\r\n%s"%escape_dots(desc))

def parse_ns_body(data):
  """Parse the body of an NS event or command into a list of
     NetworkStatus instances"""
  if not data: return []
  nsgroups = re.compile(r"^r ", re.M).split(data)
  nsgroups.pop(0)
  nslist = []
  for nsline in nsgroups:
    m = re.search(r"^s((?:[ ]\S*)+)", nsline, re.M)
    flags = m.groups()
    flags = flags[0].strip().split(" ")
    m = re.match(r"(\S+)\s(\S+)\s(\S+)\s(\S+\s\S+)\s(\S+)\s(\d+)\s(\d+)", nsline)    
    w = re.search(r"^w Bandwidth=(\d+)", nsline, re.M)
    if w:
      nslist.append(NetworkStatus(*(m.groups()+(flags,)+(int(w.group(1))*1000,))))
    else:
      nslist.append(NetworkStatus(*(m.groups() + (flags,))))
  return nslist

class EventSink:
  def heartbeat_event(self, event): pass
  def unknown_event(self, event): pass
  def circ_status_event(self, event): pass
  def stream_status_event(self, event): pass
  def stream_bw_event(self, event): pass
  def or_conn_status_event(self, event): pass
  def bandwidth_event(self, event): pass
  def new_desc_event(self, event): pass
  def msg_event(self, event): pass
  def ns_event(self, event): pass
  def new_consensus_event(self, event): pass
  def buildtimeout_set_event(self, event): pass
  def guard_event(self, event): pass
  def address_mapped_event(self, event): pass
  def timer_event(self, event): pass

class EventListener(EventSink):
  """An 'EventListener' is a passive sink for parsed Tor events. It 
     implements the same interface as EventHandler, but it should
     not alter Tor's behavior as a result of these events.
    
     Do not extend from this class. Instead, extend from one of 
     Pre, Post, or Dual event listener, to get events 
     before, after, or before and after the EventHandler handles them.
     """
  def __init__(self):
    """Create a new EventHandler."""
    self._map1 = {
      "CIRC" : self.circ_status_event,
      "STREAM" : self.stream_status_event,
      "ORCONN" : self.or_conn_status_event,
      "STREAM_BW" : self.stream_bw_event,
      "BW" : self.bandwidth_event,
      "DEBUG" : self.msg_event,
      "INFO" : self.msg_event,
      "NOTICE" : self.msg_event,
      "WARN" : self.msg_event,
      "ERR" : self.msg_event,
      "NEWDESC" : self.new_desc_event,
      "ADDRMAP" : self.address_mapped_event,
      "NS" : self.ns_event,
      "NEWCONSENSUS" : self.new_consensus_event,
      "BUILDTIMEOUT_SET" : self.buildtimeout_set_event,
      "GUARD" : self.guard_event,
      "TORCTL_TIMER" : self.timer_event
      }
    self.parent_handler = None
    self._sabotage()

  def _sabotage(self):
    raise TorCtlError("Error: Do not extend from EventListener directly! Use Pre, Post or DualEventListener instead.")
 
  def listen(self, event):
    self.heartbeat_event(event)
    self._map1.get(event.event_name, self.unknown_event)(event)

  def set_parent(self, parent_handler):
    self.parent_handler = parent_handler

class PreEventListener(EventListener):
  def _sabotage(self): pass
class PostEventListener(EventListener):
  def _sabotage(self): pass
class DualEventListener(PreEventListener,PostEventListener): 
  def _sabotage(self): pass

class EventHandler(EventSink):
  """An 'EventHandler' wraps callbacks for the events Tor can return. 
     Each event argument is an instance of the corresponding event
     class."""
  def __init__(self):
    """Create a new EventHandler."""
    self._map1 = {
      "CIRC" : self.circ_status_event,
      "STREAM" : self.stream_status_event,
      "ORCONN" : self.or_conn_status_event,
      "STREAM_BW" : self.stream_bw_event,
      "BW" : self.bandwidth_event,
      "DEBUG" : self.msg_event,
      "INFO" : self.msg_event,
      "NOTICE" : self.msg_event,
      "WARN" : self.msg_event,
      "ERR" : self.msg_event,
      "NEWDESC" : self.new_desc_event,
      "ADDRMAP" : self.address_mapped_event,
      "NS" : self.ns_event,
      "NEWCONSENSUS" : self.new_consensus_event,
      "BUILDTIMEOUT_SET" : self.buildtimeout_set_event,
      "GUARD" : self.guard_event,
      "TORCTL_TIMER" : self.timer_event
      }
    self.c = None # Gets set by Connection.set_event_hanlder()
    self.pre_listeners = []
    self.post_listeners = []

  def _handle1(self, timestamp, lines):
    """Dispatcher: called from Connection when an event is received."""
    for code, msg, data in lines:
      event = self._decode1(msg, data)
      event.arrived_at = timestamp
      event.state=EVENT_STATE.PRELISTEN
      for l in self.pre_listeners:
        l.listen(event)
      event.state=EVENT_STATE.HEARTBEAT
      self.heartbeat_event(event)
      event.state=EVENT_STATE.HANDLING
      self._map1.get(event.event_name, self.unknown_event)(event)
      event.state=EVENT_STATE.POSTLISTEN
      for l in self.post_listeners:
        l.listen(event)

  def _decode1(self, body, data):
    """Unpack an event message into a type/arguments-tuple tuple."""
    if " " in body:
      evtype,body = body.split(" ",1)
    else:
      evtype,body = body,""
    evtype = evtype.upper()
    if evtype == "CIRC":
      m = re.match(r"(\d+)\s+(\S+)(\s\S+)?(\s\S+)?(\s\S+)?(\s\S+)?", body)
      if not m:
        raise ProtocolError("CIRC event misformatted.")
      ident,status,path,purpose,reason,remote = m.groups()
      ident = int(ident)
      if path:
        if "PURPOSE=" in path:
          remote = reason
          reason = purpose
          purpose=path
          path=[]
        elif "REASON=" in path:
          remote = reason
          reason = path
          purpose = ""
          path=[]
        else:
          path_verb = path.strip().split(",")
          path = []
          for p in path_verb:
            path.append(p.replace("~", "=").split("=")[0])
      else:
        path = []

      if purpose and "REASON=" in purpose:
        remote=reason
        reason=purpose
        purpose=""

      if purpose: purpose = purpose[9:]
      if reason: reason = reason[8:]
      if remote: remote = remote[15:]
      event = CircuitEvent(evtype, ident, status, path, purpose, reason, remote)
    elif evtype == "STREAM":
      #plog("DEBUG", "STREAM: "+body)
      m = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)?:(\d+)(\sREASON=\S+)?(\sREMOTE_REASON=\S+)?(\sSOURCE=\S+)?(\sSOURCE_ADDR=\S+)?(\s+PURPOSE=\S+)?", body)
      if not m:
        raise ProtocolError("STREAM event misformatted.")
      ident,status,circ,target_host,target_port,reason,remote,source,source_addr,purpose = m.groups()
      ident,circ = map(int, (ident,circ))
      if not target_host: # This can happen on SOCKS_PROTOCOL failures
        target_host = "(none)"
      if reason: reason = reason[8:]
      if remote: remote = remote[15:]
      if source: source = source[8:]
      if source_addr: source_addr = source_addr[13:]
      if purpose:
        purpose = purpose.lstrip()
        purpose = purpose[8:]
      event = StreamEvent(evtype, ident, status, circ, target_host,
               int(target_port), reason, remote, source, source_addr, purpose)
    elif evtype == "ORCONN":
      m = re.match(r"(\S+)\s+(\S+)(\sAGE=\S+)?(\sREAD=\S+)?(\sWRITTEN=\S+)?(\sREASON=\S+)?(\sNCIRCS=\S+)?", body)
      if not m:
        raise ProtocolError("ORCONN event misformatted.")
      target, status, age, read, wrote, reason, ncircs = m.groups()

      #plog("DEBUG", "ORCONN: "+body)
      if ncircs: ncircs = int(ncircs[8:])
      else: ncircs = 0
      if reason: reason = reason[8:]
      if age: age = int(age[5:])
      else: age = 0
      if read: read = int(read[6:])
      else: read = 0
      if wrote: wrote = int(wrote[9:])
      else: wrote = 0
      event = ORConnEvent(evtype, status, target, age, read, wrote,
                reason, ncircs)
    elif evtype == "STREAM_BW":
      m = re.match(r"(\d+)\s+(\d+)\s+(\d+)", body)
      if not m:
        raise ProtocolError("STREAM_BW event misformatted.")
      event = StreamBwEvent(evtype, *m.groups())
    elif evtype == "BW":
      m = re.match(r"(\d+)\s+(\d+)", body)
      if not m:
        raise ProtocolError("BANDWIDTH event misformatted.")
      read, written = map(long, m.groups())
      event = BWEvent(evtype, read, written)
    elif evtype in ("DEBUG", "INFO", "NOTICE", "WARN", "ERR"):
      event = LogEvent(evtype, body)
    elif evtype == "NEWDESC":
      ids_verb = body.split(" ")
      ids = []
      for i in ids_verb:
        ids.append(i.replace("~", "=").split("=")[0].replace("$",""))
      event = NewDescEvent(evtype, ids)
    elif evtype == "ADDRMAP":
      # TODO: Also parse errors and GMTExpiry
      m = re.match(r'(\S+)\s+(\S+)\s+(\"[^"]+\"|\w+)', body)
      if not m:
        raise ProtocolError("ADDRMAP event misformatted.")
      fromaddr, toaddr, when = m.groups()
      if when.upper() == "NEVER":  
        when = None
      else:
        when = time.strptime(when[1:-1], "%Y-%m-%d %H:%M:%S")
      event = AddrMapEvent(evtype, fromaddr, toaddr, when)
    elif evtype == "NS":
      event = NetworkStatusEvent(evtype, parse_ns_body(data))
    elif evtype == "NEWCONSENSUS":
      event = NewConsensusEvent(evtype, parse_ns_body(data))
    elif evtype == "BUILDTIMEOUT_SET":
      m = re.match(
        r"(\S+)\sTOTAL_TIMES=(\d+)\sTIMEOUT_MS=(\d+)\sXM=(\d+)\sALPHA=(\S+)\sCUTOFF_QUANTILE=(\S+)",
        body)
      set_type, total_times, timeout_ms, xm, alpha, quantile = m.groups()
      event = BuildTimeoutSetEvent(evtype, set_type, int(total_times),
                                   int(timeout_ms), int(xm), float(alpha),
                                   float(quantile))
    elif evtype == "GUARD":
      m = re.match(r"(\S+)\s(\S+)\s(\S+)", body)
      entry, guard, status = m.groups()
      event = GuardEvent(evtype, entry, guard, status)
    elif evtype == "TORCTL_TIMER":
      event = TimerEvent(evtype, data)
    else:
      event = UnknownEvent(evtype, body)

    return event

  def add_event_listener(self, evlistener):
    if isinstance(evlistener, PreEventListener):
      self.pre_listeners.append(evlistener)
    if isinstance(evlistener, PostEventListener):
      self.post_listeners.append(evlistener)
    evlistener.set_parent(self)

  def heartbeat_event(self, event):
    """Called before any event is received. Convenience function
       for any cleanup/setup/reconfiguration you may need to do.
    """
    pass

  def unknown_event(self, event):
    """Called when we get an event type we don't recognize.  This
       is almost alwyas an error.
    """
    pass

  def circ_status_event(self, event):
    """Called when a circuit status changes if listening to CIRCSTATUS
       events."""
    pass

  def stream_status_event(self, event):
    """Called when a stream status changes if listening to STREAMSTATUS
       events.  """
    pass

  def stream_bw_event(self, event):
    pass

  def or_conn_status_event(self, event):
    """Called when an OR connection's status changes if listening to
       ORCONNSTATUS events."""
    pass

  def bandwidth_event(self, event):
    """Called once a second if listening to BANDWIDTH events.
    """
    pass

  def new_desc_event(self, event):
    """Called when Tor learns a new server descriptor if listenting to
       NEWDESC events.
    """
    pass

  def msg_event(self, event):
    """Called when a log message of a given severity arrives if listening
       to INFO_MSG, NOTICE_MSG, WARN_MSG, or ERR_MSG events."""
    pass

  def ns_event(self, event):
    pass

  def new_consensus_event(self, event):
    pass

  def buildtimeout_set_event(self, event):
    pass

  def guard_event(self, event):
    pass

  def address_mapped_event(self, event):
    """Called when Tor adds a mapping for an address if listening
       to ADDRESSMAPPED events.
    """
    pass

  def timer_event(self, event):
    pass

class Consensus:
  """
  A Consensus is a pickleable container for the members of
  ConsensusTracker. This should only be used as a temporary 
  reference, and will change after a NEWDESC or NEWCONSENUS event.
  If you want a copy of a consensus that is independent
  of subsequent updates, use copy.deepcopy()
  """

  def __init__(self, ns_map, sorted_r, router_map, nick_map, consensus_count):
    self.ns_map = ns_map
    self.sorted_r = sorted_r
    self.routers = router_map
    self.name_to_key = nick_map
    self.consensus_count = consensus_count

class ConsensusTracker(EventHandler):
  """
  A ConsensusTracker is an EventHandler that tracks the current
  consensus of Tor in self.ns_map, self.routers and self.sorted_r

  Users must subscribe to "NEWCONSENSUS" and "NEWDESC" events.

  If you also wish to track the Tor client's opinion on the Running flag
  based on reachability tests, you must subscribe to "NS" events,
  and you should set the constructor parameter "consensus_only" to
  False.
  """
  def __init__(self, c, RouterClass=Router, consensus_only=True):
    EventHandler.__init__(self)
    c.set_event_handler(self)
    self.ns_map = {}
    self.routers = {}
    self.sorted_r = []
    self.name_to_key = {}
    self.RouterClass = RouterClass
    self.consensus_count = 0
    self.consensus_only = consensus_only
    self.update_consensus()

  # XXX: If there were a potential memory leak through perpetually referenced
  # objects, this function would be the #1 suspect.
  def _read_routers(self, nslist):
    # Routers can fall out of our consensus five different ways:
    # 1. Their descriptors disappear
    # 2. Their NS documents disappear
    # 3. They lose the Running flag
    # 4. They list a bandwidth of 0
    # 5. They have 'opt hibernating' set
    routers = self.c.read_routers(nslist) # Sets .down if 3,4,5
    self.consensus_count = len(routers)
    old_idhexes = set(self.routers.keys())
    new_idhexes = set(map(lambda r: r.idhex, routers)) 
    for r in routers:
      if r.idhex in self.routers:
        if self.routers[r.idhex].nickname != r.nickname:
          plog("NOTICE", "Router "+r.idhex+" changed names from "
             +self.routers[r.idhex].nickname+" to "+r.nickname)
        # Must do IN-PLACE update to keep all the refs to this router
        # valid and current (especially for stats)
        self.routers[r.idhex].update_to(r)
      else:
        rc = self.RouterClass(r)
        self.routers[rc.idhex] = rc

    removed_idhexes = old_idhexes - new_idhexes
    removed_idhexes.update(set(map(lambda r: r.idhex,
                                   filter(lambda r: r.down, routers))))

    for i in removed_idhexes:
      if i not in self.routers: continue
      self.routers[i].down = True
      if "Running" in self.routers[i].flags:
        self.routers[i].flags.remove("Running")
      if self.routers[i].refcount == 0:
        self.routers[i].deleted = True
        if self.routers[i].__class__.__name__ == "StatsRouter":
          plog("WARN", "Expiring non-running StatsRouter "+i)
        else:
          plog("INFO", "Expiring non-running router "+i)
        del self.routers[i]
      else:
        plog("INFO", "Postponing expiring non-running router "+i)
        self.routers[i].deleted = True

    self.sorted_r = filter(lambda r: not r.down, self.routers.itervalues())
    self.sorted_r.sort(lambda x, y: cmp(y.bw, x.bw))
    for i in xrange(len(self.sorted_r)): self.sorted_r[i].list_rank = i

    # XXX: Verification only. Can be removed.
    self._sanity_check(self.sorted_r)

  def _sanity_check(self, list):
    if len(self.routers) > 1.5*self.consensus_count:
      plog("WARN", "Router count of "+str(len(self.routers))+" exceeds consensus count "+str(self.consensus_count)+" by more than 50%")

    if len(self.ns_map) < self.consensus_count:
      plog("WARN", "NS map count of "+str(len(self.ns_map))+" is below consensus count "+str(self.consensus_count))

    downed =  filter(lambda r: r.down, list)
    for d in downed:
      plog("WARN", "Router "+d.idhex+" still present but is down. Del: "+str(d.deleted)+", flags: "+str(d.flags)+", bw: "+str(d.bw))
 
    deleted =  filter(lambda r: r.deleted, list)
    for d in deleted:
      plog("WARN", "Router "+d.idhex+" still present but is deleted. Down: "+str(d.down)+", flags: "+str(d.flags)+", bw: "+str(d.bw))

    zero =  filter(lambda r: r.refcount == 0 and r.__class__.__name__ == "StatsRouter", list)
    for d in zero:
      plog("WARN", "Router "+d.idhex+" has refcount 0. Del:"+str(d.deleted)+", Down: "+str(d.down)+", flags: "+str(d.flags)+", bw: "+str(d.bw))
 
  def _update_consensus(self, nslist):
    self.ns_map = {}
    for n in nslist:
      self.ns_map[n.idhex] = n
      self.name_to_key[n.nickname] = "$"+n.idhex
   
  def update_consensus(self):
    if self.consensus_only:
      self._update_consensus(self.c.get_consensus())
    else:
      self._update_consensus(self.c.get_network_status())
    self._read_routers(self.ns_map.values())

  def new_consensus_event(self, n):
    self._update_consensus(n.nslist)
    self._read_routers(self.ns_map.values())
    plog("DEBUG", str(time.time()-n.arrived_at)+" Read " + str(len(n.nslist))
       +" NC => " + str(len(self.sorted_r)) + " routers")
 
  def new_desc_event(self, d):
    update = False
    for i in d.idlist:
      r = None
      try:
        if i in self.ns_map:
          ns = (self.ns_map[i],)
        else:
          plog("WARN", "Need to getinfo ns/id for router desc: "+i)
          ns = self.c.get_network_status("id/"+i)
        r = self.c.read_routers(ns)
      except ErrorReply, e:
        plog("WARN", "Error reply for "+i+" after NEWDESC: "+str(e))
        continue
      if not r:
        plog("WARN", "No router desc for "+i+" after NEWDESC")
        continue
      elif len(r) != 1:
        plog("WARN", "Multiple descs for "+i+" after NEWDESC")

      r = r[0]
      ns = ns[0]
      if ns.idhex in self.routers and self.routers[ns.idhex].orhash == r.orhash:
        plog("NOTICE",
             "Got extra NEWDESC event for router "+ns.nickname+"="+ns.idhex)
      else:
        self.consensus_count += 1
      self.name_to_key[ns.nickname] = "$"+ns.idhex
      if r and r.idhex in self.ns_map:
        if ns.orhash != self.ns_map[r.idhex].orhash:
          plog("WARN", "Getinfo and consensus disagree for "+r.idhex)
          continue
        update = True
        if r.idhex in self.routers:
          self.routers[r.idhex].update_to(r)
        else:
          self.routers[r.idhex] = self.RouterClass(r)
    if update:
      self.sorted_r = filter(lambda r: not r.down, self.routers.itervalues())
      self.sorted_r.sort(lambda x, y: cmp(y.bw, x.bw))
      for i in xrange(len(self.sorted_r)): self.sorted_r[i].list_rank = i
    plog("DEBUG", str(time.time()-d.arrived_at)+ " Read " + str(len(d.idlist))
       +" ND => "+str(len(self.sorted_r))+" routers. Update: "+str(update))
    # XXX: Verification only. Can be removed.
    self._sanity_check(self.sorted_r)
    return update

  def ns_event(self, ev):
    update = False
    for ns in ev.nslist:
      # Check current consensus.. If present, check flags
      if ns.idhex in self.ns_map and ns.idhex in self.routers and \
         ns.orhash == self.ns_map[ns.idhex].orhash:
        if "Running" in ns.flags and \
           "Running" not in self.ns_map[ns.idhex].flags:
          plog("INFO", "Router "+ns.nickname+"="+ns.idhex+" is now up.")
          update = True
          self.routers[ns.idhex].flags = ns.flags
          self.routers[ns.idhex].down = False

        if "Running" not in ns.flags and \
           "Running" in self.ns_map[ns.idhex].flags:
          plog("INFO", "Router "+ns.nickname+"="+ns.idhex+" is now down.")
          update = True
          self.routers[ns.idhex].flags = ns.flags
          self.routers[ns.idhex].down = True
    if update:
      self.sorted_r = filter(lambda r: not r.down, self.routers.itervalues())
      self.sorted_r.sort(lambda x, y: cmp(y.bw, x.bw))
      for i in xrange(len(self.sorted_r)): self.sorted_r[i].list_rank = i
    self._sanity_check(self.sorted_r)

  def current_consensus(self):
    return Consensus(self.ns_map, self.sorted_r, self.routers, 
                     self.name_to_key, self.consensus_count)

class DebugEventHandler(EventHandler):
  """Trivial debug event handler: reassembles all parsed events to stdout."""
  def circ_status_event(self, circ_event): # CircuitEvent()
    output = [circ_event.event_name, str(circ_event.circ_id),
          circ_event.status]
    if circ_event.path:
      output.append(",".join(circ_event.path))
    if circ_event.reason:
      output.append("REASON=" + circ_event.reason)
    if circ_event.remote_reason:
      output.append("REMOTE_REASON=" + circ_event.remote_reason)
    print " ".join(output)

  def stream_status_event(self, strm_event):
    output = [strm_event.event_name, str(strm_event.strm_id),
          strm_event.status, str(strm_event.circ_id),
          strm_event.target_host, str(strm_event.target_port)]
    if strm_event.reason:
      output.append("REASON=" + strm_event.reason)
    if strm_event.remote_reason:
      output.append("REMOTE_REASON=" + strm_event.remote_reason)
    print " ".join(output)

  def ns_event(self, ns_event):
    for ns in ns_event.nslist:
      print " ".join((ns_event.event_name, ns.nickname, ns.idhash,
        ns.updated.isoformat(), ns.ip, str(ns.orport),
        str(ns.dirport), " ".join(ns.flags)))

  def new_consensus_event(self, nc_event):
    self.ns_event(nc_event)

  def new_desc_event(self, newdesc_event):
    print " ".join((newdesc_event.event_name, " ".join(newdesc_event.idlist)))
   
  def or_conn_status_event(self, orconn_event):
    if orconn_event.age: age = "AGE="+str(orconn_event.age)
    else: age = ""
    if orconn_event.read_bytes: read = "READ="+str(orconn_event.read_bytes)
    else: read = ""
    if orconn_event.wrote_bytes: wrote = "WRITTEN="+str(orconn_event.wrote_bytes)
    else: wrote = ""
    if orconn_event.reason: reason = "REASON="+orconn_event.reason
    else: reason = ""
    if orconn_event.ncircs: ncircs = "NCIRCS="+str(orconn_event.ncircs)
    else: ncircs = ""
    print " ".join((orconn_event.event_name, orconn_event.endpoint,
            orconn_event.status, age, read, wrote, reason, ncircs))

  def msg_event(self, log_event):
    print log_event.event_name+" "+log_event.msg
  
  def bandwidth_event(self, bw_event):
    print bw_event.event_name+" "+str(bw_event.read)+" "+str(bw_event.written)

def parseHostAndPort(h):
  """Given a string of the form 'address:port' or 'address' or
     'port' or '', return a two-tuple of (address, port)
  """
  host, port = "localhost", 9100
  if ":" in h:
    i = h.index(":")
    host = h[:i]
    try:
      port = int(h[i+1:])
    except ValueError:
      print "Bad hostname %r"%h
      sys.exit(1)
  elif h:
    try:
      port = int(h)
    except ValueError:
      host = h

  return host, port

def run_example(host,port):
  """ Example of basic TorCtl usage. See PathSupport for more advanced
      usage.
  """
  print "host is %s:%d"%(host,port)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host,port))
  c = Connection(s)
  c.set_event_handler(DebugEventHandler())
  th = c.launch_thread()
  c.authenticate()
  print "nick",`c.get_option("nickname")`
  print `c.get_info("version")`
  #print `c.get_info("desc/name/moria1")`
  print `c.get_info("network-status")`
  print `c.get_info("addr-mappings/all")`
  print `c.get_info("addr-mappings/config")`
  print `c.get_info("addr-mappings/cache")`
  print `c.get_info("addr-mappings/control")`

  print `c.extend_circuit(0,["moria1"])`
  try:
    print `c.extend_circuit(0,[""])`
  except ErrorReply: # wtf?
    print "got error. good."
  except:
    print "Strange error", sys.exc_info()[0]
   
  #send_signal(s,1)
  #save_conf(s)

  #set_option(s,"1")
  #set_option(s,"bandwidthburstbytes 100000")
  #set_option(s,"runasdaemon 1")
  #set_events(s,[EVENT_TYPE.WARN])
#  c.set_events([EVENT_TYPE.ORCONN], True)
  c.set_events([EVENT_TYPE.STREAM, EVENT_TYPE.CIRC,
          EVENT_TYPE.NEWCONSENSUS, EVENT_TYPE.NEWDESC,
          EVENT_TYPE.ORCONN, EVENT_TYPE.BW], True)

  th.join()
  return

if __name__ == '__main__':
  if len(sys.argv) > 2:
    print "Syntax: TorControl.py torhost:torport"
    sys.exit(0)
  else:
    sys.argv.append("localhost:9051")
  sh,sp = parseHostAndPort(sys.argv[1])
  run_example(sh,sp)

