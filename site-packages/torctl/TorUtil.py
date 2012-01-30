#!/usr/bin/python
# TorCtl.py -- Python module to interface with Tor Control interface.
# Copyright 2007-2010 Mike Perry -- See LICENSE for licensing information.
# Portions Copyright 2005 Nick Mathewson

"""
TorUtil -- Support functions for TorCtl.py and metatroller
"""

import os
import re
import sys
import socket
import binascii
import math
import time
import logging
import ConfigParser

if sys.version_info < (2, 5):
  from sha import sha as sha1
else:
  from hashlib import sha1

__all__ = ["Enum", "Enum2", "Callable", "sort_list", "quote", "escape_dots", "unescape_dots",
      "BufSock", "secret_to_key", "urandom_rng", "s2k_gen", "s2k_check", "plog", 
     "ListenSocket", "zprob", "logfile", "loglevel", "loglevels"]

# TODO: This isn't the right place for these.. But at least it's unified.
tor_port = 9060
tor_host = '127.0.0.1'

control_port = 9061
control_host = '127.0.0.1'
control_pass = ""

meta_port = 9052
meta_host = '127.0.0.1'

class Referrer:
  def __init__(self, cl):
    self.referrers = {}
    self.cl_name = cl
    self.count = 0

  def recurse_store(self, gc, obj, depth, max_depth):
    if depth >= max_depth: return
    for r in gc.get_referrers(obj):
      if hasattr(r, "__class__"):
        cl = r.__class__.__name__
        # Skip frames and list iterators.. prob just us
        if cl in ("frame", "listiterator"): continue 
        if cl not in self.referrers:
          self.referrers[cl] = Referrer(cl)
        self.referrers[cl].count += 1
        self.referrers[cl].recurse_store(gc, r, depth+1, max_depth)

  def recurse_print(self, rcutoff, depth=""):
    refs = self.referrers.keys()
    refs.sort(lambda x, y: self.referrers[y].count - self.referrers[x].count)
    for r in refs:
      if self.referrers[r].count > rcutoff:
        plog("NOTICE", "GC:  "+depth+"Refed by "+r+": "+str(self.referrers[r].count))
        self.referrers[r].recurse_print(rcutoff, depth+" ")

def dump_class_ref_counts(referrer_depth=2, cutoff=500, rcutoff=1,
        ignore=('tuple', 'list', 'function', 'dict',
                 'builtin_function_or_method',
                 'wrapper_descriptor')):
  """ Debugging function to track down types of objects
      that cannot be garbage collected because we hold refs to them 
      somewhere."""
  import gc
  __dump_class_ref_counts(gc, referrer_depth, cutoff, rcutoff, ignore)
  gc.collect()
  plog("NOTICE", "GC: Done.")

def __dump_class_ref_counts(gc, referrer_depth, cutoff, rcutoff, ignore):
  """ loil
  """
  plog("NOTICE", "GC: Gathering garbage collection stats...")
  uncollectable = gc.collect()
  class_counts = {}
  referrers = {}
  plog("NOTICE", "GC: Uncollectable objects: "+str(uncollectable))
  objs = gc.get_objects()
  for obj in objs:
    if hasattr(obj, "__class__"):
      cl = obj.__class__.__name__
      if cl in ignore: continue
      if cl not in class_counts:
        class_counts[cl] = 0
        referrers[cl] = Referrer(cl)
      class_counts[cl] += 1
  if referrer_depth:
    for obj in objs:
      if hasattr(obj, "__class__"):
        cl = obj.__class__.__name__
        if cl in ignore: continue
        if class_counts[cl] > cutoff:
          referrers[cl].recurse_store(gc, obj, 0, referrer_depth)
  classes = class_counts.keys()
  classes.sort(lambda x, y: class_counts[y] - class_counts[x])
  for c in classes:
    if class_counts[c] < cutoff: continue
    plog("NOTICE", "GC: Class "+c+": "+str(class_counts[c]))
    if referrer_depth:
      referrers[c].recurse_print(rcutoff)



def read_config(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)
  global tor_port, tor_host, control_port, control_pass, control_host
  global meta_port, meta_host
  global loglevel

  tor_port = config.getint('TorCtl', 'tor_port')
  meta_port = config.getint('TorCtl', 'meta_port')
  control_port = config.getint('TorCtl', 'control_port')

  tor_host = config.get('TorCtl', 'tor_host')
  control_host = config.get('TorCtl', 'control_host')
  meta_host = config.get('TorCtl', 'meta_host')
  control_pass = config.get('TorCtl', 'control_pass')
  loglevel = config.get('TorCtl', 'loglevel')


class Enum:
  """ Defines an ordered dense name-to-number 1-1 mapping """
  def __init__(self, start, names):
    self.nameOf = {}
    idx = start
    for name in names:
      setattr(self,name,idx)
      self.nameOf[idx] = name
      idx += 1

class Enum2:
  """ Defines an ordered sparse name-to-number 1-1 mapping """
  def __init__(self, **args):
    self.__dict__.update(args)
    self.nameOf = {}
    for k,v in args.items():
      self.nameOf[v] = k

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

def sort_list(list, key):
  """ Sort a list by a specified key """
  list.sort(lambda x,y: cmp(key(x), key(y))) # Python < 2.4 hack
  return list

def quote(s):
  return re.sub(r'([\r\n\\\"])', r'\\\1', s)

def escape_dots(s, translate_nl=1):
  if translate_nl:
    lines = re.split(r"\r?\n", s)
  else:
    lines = s.split("\r\n")
  if lines and not lines[-1]:
    del lines[-1]
  for i in xrange(len(lines)):
    if lines[i].startswith("."):
      lines[i] = "."+lines[i]
  lines.append(".\r\n")
  return "\r\n".join(lines)

def unescape_dots(s, translate_nl=1):
  lines = s.split("\r\n")

  for i in xrange(len(lines)):
    if lines[i].startswith("."):
      lines[i] = lines[i][1:]

  if lines and lines[-1]:
    lines.append("")

  if translate_nl:
    return "\n".join(lines)
  else:
    return "\r\n".join(lines)

# XXX: Exception handling
class BufSock:
  def __init__(self, s):
    self._s = s
    self._buf = []

  def readline(self):
    if self._buf:
      idx = self._buf[0].find('\n')
      if idx >= 0:
        result = self._buf[0][:idx+1]
        self._buf[0] = self._buf[0][idx+1:]
        return result

    while 1:
      s = self._s.recv(128)
      if not s: return None
      # XXX: This really does need an exception
      #  raise ConnectionClosed()
      idx = s.find('\n')
      if idx >= 0:
        self._buf.append(s[:idx+1])
        result = "".join(self._buf)
        rest = s[idx+1:]
        if rest:
          self._buf = [ rest ]
        else:
          del self._buf[:]
        return result
      else:
        self._buf.append(s)

  def write(self, s):
    self._s.send(s)

  def close(self):
    self._s.close()

# SocketServer.TCPServer is nuts.. 
class ListenSocket:
  def __init__(self, listen_ip, port):
    msg = None
    self.s = None
    for res in socket.getaddrinfo(listen_ip, port, socket.AF_UNSPEC,
              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
      af, socktype, proto, canonname, sa = res
      try:
        self.s = socket.socket(af, socktype, proto)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      except socket.error, msg:
        self.s = None
        continue
      try:
        self.s.bind(sa)
        self.s.listen(1)
      except socket.error, msg:
        self.s.close()
        self.s = None
        continue
      break
    if self.s is None:
      raise socket.error(msg)

  def accept(self):
    conn, addr = self.s.accept()
    return conn

  def close(self):
    self.s.close()


def secret_to_key(secret, s2k_specifier):
  """Used to generate a hashed password string. DOCDOC."""
  c = ord(s2k_specifier[8])
  EXPBIAS = 6
  count = (16+(c&15)) << ((c>>4) + EXPBIAS)

  d = sha1()
  tmp = s2k_specifier[:8]+secret
  slen = len(tmp)
  while count:
    if count > slen:
      d.update(tmp)
      count -= slen
    else:
      d.update(tmp[:count])
      count = 0
  return d.digest()

def urandom_rng(n):
  """Try to read some entropy from the platform entropy source."""
  f = open('/dev/urandom', 'rb')
  try:
    return f.read(n)
  finally:
    f.close()

def s2k_gen(secret, rng=None):
  """DOCDOC"""
  if rng is None:
    if hasattr(os, "urandom"):
      rng = os.urandom
    else:
      rng = urandom_rng
  spec = "%s%s"%(rng(8), chr(96))
  return "16:%s"%(
    binascii.b2a_hex(spec + secret_to_key(secret, spec)))

def s2k_check(secret, k):
  """DOCDOC"""
  assert k[:3] == "16:"

  k =  binascii.a2b_hex(k[3:])
  return secret_to_key(secret, k[:9]) == k[9:]

## XXX: Make this a class?
loglevel = "DEBUG"
#loglevels = {"DEBUG" : 0, "INFO" : 1, "NOTICE" : 2, "WARN" : 3, "ERROR" : 4, "NONE" : 5}
logfile = None
logger = None

# Python logging levels are in increments of 10, so place our custom
# levels in between Python's default levels.
loglevels = { "DEBUG":  logging.DEBUG,
              "INFO":   logging.INFO,
              "NOTICE": logging.INFO + 5,
              "WARN":   logging.WARN,
              "ERROR":  logging.ERROR,
              "NONE":   logging.ERROR + 5 }
# Set loglevel => name translation.
for name, value in loglevels.iteritems():
  logging.addLevelName(value, name)

def plog_use_logger(name):
  """ Set the Python logger to use with plog() by name.
      Useful when TorCtl is integrated with an application using logging.
      The logger specified by name must be set up before the first call
      to plog()! """
  global logger, loglevels
  logger = logging.getLogger(name)

def plog(level, msg, *args):
  global logger, logfile
  if not logger:
    # Default init = old TorCtl format + default behavior
    # Default behavior = log to stdout if TorUtil.logfile is None,
    # or to the open file specified otherwise.
    logger = logging.getLogger("TorCtl")
    formatter = logging.Formatter("%(levelname)s[%(asctime)s]:%(message)s",
                                  "%a %b %d %H:%M:%S %Y")

    if not logfile:
      logfile = sys.stdout
    # HACK: if logfile is a string, assume is it the desired filename.
    if type(logfile) is str:
      f = logging.FileHandler(logfile)
      f.setFormatter(formatter)
      logger.addHandler(f)
    # otherwise, pretend it is a stream.
    else:
      ch = logging.StreamHandler(logfile)
      ch.setFormatter(formatter)
      logger.addHandler(ch)
    logger.setLevel(loglevels[loglevel])

  logger.log(loglevels[level], msg, *args)

# The following zprob routine was stolen from
# http://www.nmr.mgh.harvard.edu/Neural_Systems_Group/gary/python/stats.py
# pursuant to this license:
#
# Copyright (c) 1999-2007 Gary Strangman; All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The above license applies only to the following 39 lines of code.
def zprob(z):
    """
Returns the area under the normal curve 'to the left of' the given z value.
Thus, 
    for z<0, zprob(z) = 1-tail probability
    for z>0, 1.0-zprob(z) = 1-tail probability
    for any z, 2.0*(1.0-zprob(abs(z))) = 2-tail probability
Adapted from z.c in Gary Perlman's |Stat.

Usage:   lzprob(z)
"""
    Z_MAX = 6.0    # maximum meaningful z-value
    if z == 0.0:
        x = 0.0
    else:
        y = 0.5 * math.fabs(z)
        if y >= (Z_MAX*0.5):
            x = 1.0
        elif (y < 1.0):
            w = y*y
            x = ((((((((0.000124818987 * w
                        -0.001075204047) * w +0.005198775019) * w
                      -0.019198292004) * w +0.059054035642) * w
                    -0.151968751364) * w +0.319152932694) * w
                  -0.531923007300) * w +0.797884560593) * y * 2.0
        else:
            y = y - 2.0
            x = (((((((((((((-0.000045255659 * y
                             +0.000152529290) * y -0.000019538132) * y
                           -0.000676904986) * y +0.001390604284) * y
                         -0.000794620820) * y -0.002034254874) * y
                       +0.006549791214) * y -0.010557625006) * y
                     +0.011630447319) * y -0.009279453341) * y
                   +0.005353579108) * y -0.002141268741) * y
                 +0.000535310849) * y +0.999936657524
    if z > 0.0:
        prob = ((x+1.0)*0.5)
    else:
        prob = ((1.0-x)*0.5)
    return prob

