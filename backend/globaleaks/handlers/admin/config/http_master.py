import json
import multiprocessing
import os
import signal
import socket
import sys

from sys import executable

from twisted.internet import reactor, ssl, task, protocol
from twisted.protocols import tls
from twisted.python.compat import urllib_parse, urlquote
from twisted.web import proxy, resource, server

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from OpenSSL._util import lib as _lib, ffi as _ffi

def openListeningSocket(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(False)
    s.bind((ip, port))
    s.listen(1024)
    return s

def instantiate_subprocess(config, pool, fd):
    pp = ConfigureProtocol(config, pool)

    path = '/home/nskelsey/projects/globaleaks/backend/bin/http_worker.py'
    pp.process = reactor.spawnProcess(pp,
                                      executable,
                                      [executable, path],
                                      childFDs={0:0, 1:1, 2: "w", 3: fd},
                                      env=os.environ)
    print('Launching: %s; %s' % (pp, pp.process))
    pool.append(pp)

def instantiate_pool(config, fd):
    process_pool = []
    for i in range(multiprocessing.cpu_count()):
        pp = instantiate_subprocess(config, process_pool, fd)
        process_pool.append(pp)
    return process_pool


class ConfigureProtocol(protocol.ProcessProtocol):
  def __init__(self, cfg, process_pool):
    self.cfg = json.dumps(cfg)
    self.process_pool = process_pool

  def connectionMade(self):
    self.transport.writeToChild(2, self.cfg)
    self.transport.closeChildFD(2)
  
  def processExited(self, reason):
    global quitting

    for index, item in enumerate(self.process_pool):
        if item == self:
            self.process_pool.pop(index)
            break

    if not quitting:
        instantiate_subprocess()

    if len(self.process_pool) == 0:
        try:
            #reactor.stop()
            print('reactor stop should be called here')
        except Exception:
            pass


def SigQUIT(SIG, FRM):
    global quitting
    print('SigQUIT called for %s:%s' % SIG, FRM)
    try:
        quitting = True

        #for pp in pool:
        #    pp.process.signalProcess("INT")
        
        reactor.stop()
    except Exception as e:
        print(e)
        pass

quitting = False

#signal.signal(signal.SIGUSR1, SigQUIT)
#signal.signal(signal.SIGTERM, SigQUIT)
#signal.signal(signal.SIGINT, SigQUIT)

def launch_workers(config, priv_key, cert, chain, dh_param):
    config = {
      'ip': '127.0.0.1',
      'port': 40000,
      'ssl_key': priv_key,
      'ssl_cert': cert,
      'ssl_intermediate': chain,
      'ssl_dh': dh_param,
      'ssl_cipher_list': 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA'
    }

    s = openListeningSocket(config['ip'], config['port'])

    fd = s.fileno()
    print('Passing fd: %s'%fd)

    pool = instantiate_pool(config, fd)

    #reactor.run()
