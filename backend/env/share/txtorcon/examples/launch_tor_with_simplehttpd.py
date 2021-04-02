#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Create a new tor node and add a simple http server to it, serving a given
directory over http. The server is single-threaded and very limited.

There are two arguments that can be passed via the commandline:
    -p\tThe internet-facing port the hidden service should listen on
    -d\tThe directory to serve via http

Example:
    ./launch_tor_with_simplehttpd.py -p 8080 -d /opt/files/
'''

from __future__ import print_function

import SimpleHTTPServer
import SocketServer
import functools
import getopt
import os
import sys
import tempfile
import thread

from twisted.internet import reactor

import txtorcon


def print_help():
    print(__doc__)


def print_tor_updates(prog, tag, summary):
    # Prints some status messages while booting tor
    print('Tor booting [%d%%]: %s' % (prog, summary))


def start_httpd(httpd):
    # Create a new thread to serve requests
    print('Starting httpd...')
    return thread.start_new_thread(httpd.serve_forever, ())


def stop_httpd(httpd):
    # Kill the httpd
    print('Stopping httpd...')
    httpd.shutdown()


def setup_complete(config, port, proto):
    # Callback from twisted when tor has booted.
    # We create a reference to this function via functools.partial that
    # provides us with a reference to 'config' and 'port', twisted then adds
    # the 'proto' argument
    print('\nTor is now running. The hidden service is available at')
    print('\n\thttp://%s:%i\n' % (config.HiddenServices[0].hostname, port))
    # This is probably more secure than any other httpd...
    print('## DO NOT RELY ON THIS SERVER TO TRANSFER FILES IN A SECURE WAY ##')


def setup_failed(arg):
    # Callback from twisted if tor could not boot. Nothing to see here, move
    # along.
    print('Failed to launch tor', arg)
    reactor.stop()


def main():
    # Parse the commandline-options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:p:')
    except getopt.GetoptError as excp:
        print(str(excp))
        print_help()
        return 1

    serve_directory = '.'  # The default directory to serve files from
    hs_public_port = 8011  # The port the hidden service is available on
    web_port = 4711  # The real server's local port
    web_host = '127.0.0.1'  # The real server is bound to localhost
    for o, a in opts:
        if o == '-d':
            serve_directory = a
        elif o == '-p':
            hs_public_port = int(a)
        elif o == '-h':
            print_help()
            return
        else:
            print('Unknown option "%s"' % (o, ))
            return 1

    # Sanitize path and set working directory there (for SimpleHTTPServer)
    serve_directory = os.path.abspath(serve_directory)
    if not os.path.exists(serve_directory):
        print('Path "%s" does not exists, can\'t serve from there...' % \
            (serve_directory, ))
        return 1
    os.chdir(serve_directory)

    # Create a new SimpleHTTPServer and serve it from another thread.
    # We create a callback to Twisted to shut it down when we exit.
    print('Serving "%s" on %s:%i' % (serve_directory, web_host, web_port))
    httpd = SocketServer.TCPServer((web_host, web_port),
                                   SimpleHTTPServer.SimpleHTTPRequestHandler)
    start_httpd(httpd)
    reactor.addSystemEventTrigger(
        'before', 'shutdown',
        stop_httpd, httpd=httpd,
    )

    # Create a directory to hold our hidden service. Twisted will unlink it
    # when we exit.
    hs_temp = tempfile.mkdtemp(prefix='torhiddenservice')
    reactor.addSystemEventTrigger(
        'before', 'shutdown',
        functools.partial(txtorcon.util.delete_file_or_tree, hs_temp)
    )

    # Add the hidden service to a blank configuration
    config = txtorcon.TorConfig()
    config.SOCKSPort = 0
    config.ORPort = 9089
    config.HiddenServices = [
        txtorcon.HiddenService(
            config, hs_temp,
            ports=['%i %s:%i' % (hs_public_port, web_host, web_port)]
        )
    ]
    config.save()

    # Now launch tor
    # Notice that we use a partial function as a callback so we have a
    # reference to the config object when tor is fully running.
    tordeferred = txtorcon.launch_tor(config, reactor,
                                      progress_updates=print_tor_updates)
    tordeferred.addCallback(functools.partial(setup_complete, config,
                                              hs_public_port))
    tordeferred.addErrback(setup_failed)

    reactor.run()


if __name__ == '__main__':
    sys.exit(main())
