# -*- coding: UTF-8
#   api
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE file
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.
from globaleaks import config
from globaleaks.rest.handlers import *
from globaleaks.submission import Submission
from cyclone.web import StaticFileHandler

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
    (r'/submission', submissionHandler,
                     dict(action='new',
                          supportedMethods=['GET']
                         )),

    (r'/submission/(' + submission_id_regexp + ')',
                     submissionHandler,
                     dict(action='new',
                          supportedMethods=['GET']
                         )),

    (r'/submission/(' + submission_id_regexp + ')/fields',
                     submissionHandler,
                     dict(action='fields',
                          supportedMethods=['GET', 'POST']
                         )),

    (r'/submission/(' + submission_id_regexp + ')/groups',
                     submissionHandler,
                     dict(action='groups',
                          supportedMethods=['GET', 'POST']
                         )),

    (r'/submission/(' + submission_id_regexp + ')/files',
                     submissionHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST']
                         )),

    (r'/submission/(' + submission_id_regexp + ')/finalize',
                     submissionHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    (r'/submission/(' + submission_id_regexp + ')/status',
                     submissionHandler,
                     dict(action='status',
                          supportedMethods=['GET', 'POST']
                         )),

    ## Tip Handlers ##
    #  * /tip/<ID>/
    #  * /tip/<ID>/comment
    #  * /tip/<ID>/files
    #  * /tip/<ID>/finalize
    #  * /tip/<ID>/download
    #  * /tip/<ID>/pertinence
    (r'/tip/(' + tip_regexp + ')',
                     tipHandler,
                     dict(action='main',
                          supportedMethods=['GET', 'DELETE']
                         )),

    (r'/tip/(' + tip_regexp + ')/comment',
                     tipHandler,
                     dict(action='comment',
                          supportedMethods=['POST']
                         )),

    (r'/tip/(' + tip_regexp + ')/files',
                     tipHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST']
                         )),

    (r'/tip/(' + tip_regexp + ')/finalize',
                     tipHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    (r'/tip/(' + tip_regexp + ')/download',
                     tipHandler,
                     dict(action='dowload',
                          supportedMethods=['GET']
                         )),

    (r'/tip/(' + tip_regexp + ')/pertinence',
                     tipHandler,
                     dict(action='pertinence',
                          supportedMethods=['GET']
                         )),

    ## Receiver Handlers ##
    #  * /reciever/<ID>/
    #  * /receiver/<ID>/<MODULE>
    (r'/receiver/(' + tip_regexp + ')',
                     receiverHandler,
                     dict(action='main',
                          supportedMethods=['GET']
                         )),

    (r'/receiver/(' + tip_regexp + ')/(' + module_regexp + ')',
                     receiverHandler,
                     dict(action='module',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),

    ## Admin Handlers ##
    #  * /admin/node
    #  * /admin/contexts
    #  * /admin/groups/<ID>
    #  * /admin/receivers/<ID>
    #  * /admin/modules/<MODULE>
    (r'/admin/node', adminHandler,
                        dict(action='node',
                             supportedMethods=['GET']
                            )),

    (r'/admin/contexts', adminHandler,
                        dict(action='context',
                             supportedMethods=['GET']
                            )),
    (r'/admin/groups/(' + id_regexp + ')',
                    adminHandler,
                    dict(action='groups',
                         supportedMethods=['GET']
                        )),

    (r'/admin/receivers/(' + id_regexp + ')',
                    adminHandler,
                    dict(action='receivers',
                         supportedMethods=['GET']
                        )),

    (r'/admin/modules/(' + module_regexp + ')', adminHandler,
                    dict(action='module',
                         supportedMethods=['GET']
                        )),
    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.glbackend.glclient_path})
    ]

