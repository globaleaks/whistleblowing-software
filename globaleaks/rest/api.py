import json
from twisted.web import resource
from globaleaks.rest.handlers import *
from cyclone.web import Application

"""
The follwing part of code is intended to be moved in the
backend/core logic, and implemented here just for
"""

if __name__ == "__main__":

    from twisted.internet import reactor
    from twisted.web import server


    # not all APIs are know at the start of the software,
    # modules can implement their own REST

    tip_regexp = '\w+'
    module_regexp = '\w+'
    id_regexp = '\w+'
    API = [(r'/node', nodeHandler),
        #= Submission Handlers
        #  * /submission/<ID>/
        #  * /submission/<ID>/fields
        #  * /submission/<ID>/groups
        #  * /submission/<ID>/finalize
        (r'/submission', submissionHandler, dict(action='new')),
        (r'/submission/(' + tip_regexp + ')',
                         submissionHandler, dict(action='new')),
        (r'/submission/(' + tip_regexp + ')/fields',
                         submissionHandler, dict(action='fields')),
        (r'/submission/(' + tip_regexp + ')/groups',
                         submissionHandler, dict(action='groups')),
        (r'/submission/(' + tip_regexp + ')/files',
                         submissionHandler, dict(action='files')),
        (r'/submission/(' + tip_regexp + ')/finalize',
                         submissionHandler, dict(action='finalize')),

        #= Tip Handlers
        #  * /tip/<ID>/
        #  * /tip/<ID>/comment
        #  * /tip/<ID>/files
        #  * /tip/<ID>/finalize
        #  * /tip/<ID>/download
        #  * /tip/<ID>/pertinence
        (r'/tip/(' + tip_regexp + ')',
                         tipHandler, dict(action='main')),
        (r'/tip/(' + tip_regexp + ')/comment',
                         tipHandler, dict(action='comment')),
        (r'/tip/(' + tip_regexp + ')/files',
                         tipHandler, dict(action='files')),
        (r'/tip/(' + tip_regexp + ')/finalize',
                         tipHandler, dict(action='finalize')),
        (r'/tip/(' + tip_regexp + ')/download',
                         tipHandler, dict(action='dowload')),
        (r'/tip/(' + tip_regexp + ')/pertinence',
                         tipHandler, dict(action='pertinence')),

        #= Receiver Handlers
        #  * /reciever/<ID>/
        #  * /receiver/<ID>/<MODULE>
        (r'/receiver/(' + tip_regexp + ')',
                         receiverHandler, dict(action='main')),
        (r'/receiver/(' + tip_regexp + ')/(' + module_regexp + ')',
                         receiverHandler, dict(action='module')),

        #= Admin Handlers
        #  * /admin/node
        #  * /admin/contexts
        #  * /admin/groups/<ID>
        #  * /admin/receivers/<ID>
        #  * /admin/modules/<MODULE>
        (r'/admin/node',
                        adminHandler, dict(action='node')),
        (r'/admin/contexts',
                        adminHandler, dict(action='context')),
        (r'/admin/groups/(' + id_regexp + ')',
                        adminHandler, dict(action='groups')),
        (r'/admin/receivers/(' + id_regexp + ')',
                        adminHandler, dict(action='receivers')),
        (r'/admin/modules/(' + module_regexp + ')', adminHandler,
            dict(action='module'))]

    application = Application(API)
    reactor.listenTCP(8082, application)
    reactor.run()

