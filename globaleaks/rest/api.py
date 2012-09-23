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

# long sha hash, fixed len
tip_regexp = '(\w+)'

# temporary long int or so far
submission_id_regexp = '(\w+)'

# <user_modulename>
user_module_regexp = '(notification|delivery)'

# <admin_modulename>
admin_module_regexp = '(notification|delivery|inputfilter)'

# simple uniq id, not a security issue for be not guessable
context_id_regexp = '(\w+)'


spec = [
    ## Node Handler ##
    #  * /node U1
    (r'/node', nodeHandler,
                     dict(action='root',
                          supportedMethods=['GET']
                         )),

    ## Submission Handlers ##
    #  * /submission/<ID>/ U2
    (r'/submission', submissionHandler,
                     dict(action='root',
                          supportedMethods=['GET']
                         )),

    #  * /submission/<ID>/status U3
    (r'/submission/' + submission_id_regexp + '/status',
                     submissionHandler,
                     dict(action='status',
                          supportedMethods=['GET', 'POST']
                         )),

    #  * /submission/<ID>/finalize U4
    (r'/submission/' + submission_id_regexp + '/finalize',
                     submissionHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    #  * /submission/<ID>/files U5
    (r'/submission/' + submission_id_regexp + '/files',
                     submissionHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),
    # https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    ## Tip Handlers ##
    #  * /tip/<ID>/ T1
    (r'/tip/' + tip_regexp, tipHandler,
                     dict(action='root',
                          supportedMethods=['GET', 'POST']
                         )),

    #  * /tip/<ID>/comment T2
    (r'/tip/' + tip_regexp + '/comment',
                     tipHandler,
                     dict(action='comment',
                          supportedMethods=['POST']
                         )),

    #  * /tip/<ID>/files T3
    (r'/tip/' + tip_regexp + '/files',
                     tipHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),

    #  * /tip/<ID>/finalize T4
    (r'/tip/' + tip_regexp + '/finalize',
                     tipHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    #  * /tip/<ID>/download T5
    (r'/tip/' + tip_regexp + '/download',
                     tipHandler,
                     dict(action='download',
                          supportedMethods=['GET']
                         )),

    #  * /tip/<ID>/pertinence T6
    (r'/tip/' + tip_regexp + '/pertinence',
                     tipHandler,
                     dict(action='pertinence',
                          supportedMethods=['GET']
                         )),

    ## Receiver Handlers ##
    #  * /reciever/<ID>/ R1
    (r'/receiver/' + tip_regexp, receiverHandler,
                     dict(action='root',
                          supportedMethods=['GET']
                         )),

    #  * /receiver/<TIP ID>/<user moduletype> R2
    (r'/receiver/' + tip_regexp + '/' + user_module_regexp,
                     receiverHandler,
                     dict(action='module',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),

    ## Admin Handlers ##
    #  * /admin/node A1
    (r'/admin/node', adminHandler,
                        dict(action='node',
                             supportedMethods=['GET', 'POST']
                            )),

    #  * /admin/contexts A2
    (r'/admin/contexts/' + context_id_regexp,
                        adminHandler,
                        dict(action='contexts',
                             supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                            )),

    #  * /admin/receivers/<context_ID> A3
    (r'/admin/receivers/' + context_id_regexp,
                    adminHandler,
                    dict(action='receivers',
                         supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                        )),

    #  * /admin/modules/<context_ID>/<MODULE TYPE> A4
    (r'/admin/modules/' + context_id_regexp + '/' + admin_module_regexp,
                    adminHandler,
                    dict(action='modules',
                         supportedMethods=['GET', 'POST']
                        )),

    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.glbackend.glclient_path})
    ]

