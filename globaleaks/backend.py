# -*- coding: UTF-8
#   backend
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
import sys
import os

# hack to add globaleaks to the sys path
# this would avoid export PYTHONPATH=`pwd`
cwd = '/'.join(__file__.split('/')[:-1])
sys.path.insert(0, os.path.join(cwd, '../'))

from twisted.internet.defer import inlineCallbacks
from globaleaks.db import createTables, threadpool
from globaleaks.rest import api

if __name__ == "__main__":
    """
    if invoked directly we will run the application.
    """
    from twisted.internet import reactor
    from twisted.python import log
    from cyclone.web import Application

    def start_backend(*arg):
        log.startLogging(sys.stdout)
        application = Application(api.spec, debug=True)
        reactor.listenTCP(8082, application)
        reactor.addSystemEventTrigger('after', 'shutdown', threadpool.stop)

    d = createTables()
    d.addCallback(start_backend)

    reactor.run()

