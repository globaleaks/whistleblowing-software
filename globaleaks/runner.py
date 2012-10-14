# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.python import log
from twisted.application import service, internet, app
from twisted.python.runtime import platformType

from globaleaks.db import createTables

if platformType == "win32":
    from twisted.scripts._twistw import ServerOptions, \
        WindowsApplicationRunner
    class GLBaseRunner(WindowsApplicationRunner):
        def postApplication(self):
            def runApp(res):
                service.IService(self.application).privilegedStartService()
                app.startApplication(self.application, not self.config['no_save'])
                app.startApplication(internet.TimerService(0.1, lambda:None), 0)

            print "WARNING! Windows is not tested!"
            d = createTables()
            d.addCallback(runApp)

            self.startReactor(None, self.oldstdout, self.oldstderr)
            log.msg("Server Shut Down.")
else:
    from twisted.scripts._twistd_unix import ServerOptions, \
        UnixApplicationRunner
    ServerOptions = ServerOptions
    class GLBaseRunner(UnixApplicationRunner):
        def postApplication(self):
            def runApp(res):
                self.startApplication(self.application)
                print "GLBackend is now running"
                print "Visit http://127.0.0.1:8082/index.html to interact with me"

            d = createTables()
            d.addBoth(runApp)

            self.startReactor(None, self.oldstdout, self.oldstderr)
            self.removePID(self.config['pidfile'])

