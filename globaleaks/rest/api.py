"""
    api
    ***

    This contains the specification of the API.
    Read this if you want to have an overall view of what API calls are handled
    by what.
"""


from globaleaks.rest.handlers import *
from globaleaks.submission import Submission
from cyclone.web import Application

tip_regexp = '\w+'
submission_id_regexp = '\w+'
module_regexp = '\w+'
id_regexp = '\w+'
spec = [
    ## Node Handler ##
    #  * /node
    (r'/node', nodeHandler),
    ## Submission Handlers ##
    #  * /submission/<ID>/
    #  * /submission/<ID>/fields
    #  * /submission/<ID>/groups
    #  * /submission/<ID>/files
    #  * /submission/<ID>/finalize
    #  * /submission/<ID>/status
    (r'/submission', submissionHandler, dict(action='new')),
    (r'/submission/(' + submission_id_regexp + ')',
                     submissionHandler, dict(action='new')),
    (r'/submission/(' + submission_id_regexp + ')/fields',
                     submissionHandler, dict(action='fields')),
    (r'/submission/(' + submission_id_regexp + ')/groups',
                     submissionHandler, dict(action='groups')),
    (r'/submission/(' + submission_id_regexp + ')/files',
                     submissionHandler, dict(action='files')),
    (r'/submission/(' + submission_id_regexp + ')/finalize',
                     submissionHandler, dict(action='finalize')),
    (r'/submission/(' + submission_id_regexp + ')/status',
                     submissionHandler, dict(action='status')),

    ## Tip Handlers ##
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

    ## Receiver Handlers ##
    #  * /reciever/<ID>/
    #  * /receiver/<ID>/<MODULE>
    (r'/receiver/(' + tip_regexp + ')',
                     receiverHandler, dict(action='main')),
    (r'/receiver/(' + tip_regexp + ')/(' + module_regexp + ')',
                     receiverHandler, dict(action='module')),

    ## Admin Handlers ##
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

if __name__ == "__main__":
    """
    if invoked directly we will run the application.

    XXX remove after having debugged.
    """

    from twisted.internet import reactor

    application = Application(spec)
    reactor.listenTCP(8082, application)
    reactor.run()

