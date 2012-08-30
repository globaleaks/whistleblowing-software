# -*- coding: UTF-8
#   backend
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
import sys
import os
print __file__
# hack to add globaleaks to the sys path
cwd = '/'.join(__file__.split('/')[:-1])
sys.path.insert(0, os.path.join(cwd, '../'))
sys.path.insert(0, '/home/x/code/web/cyclone')

from globaleaks.rest import api

if __name__ == "__main__":
    """
    if invoked directly we will run the application.
    """
    from twisted.internet import reactor
    from twisted.python import log
    from cyclone.web import Application

    log.startLogging(sys.stdout)

    application = Application(api.spec, debug=True)
    reactor.listenTCP(8082, application)
    reactor.run()
