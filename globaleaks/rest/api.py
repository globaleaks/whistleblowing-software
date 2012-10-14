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

from globaleaks.handlers import node, submission, tip, admin, receiver

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
    (r'/node', node.Node),

    ## Submission Handlers ##
    #  * /submission/ U2
    (r'/submission', submission.SubmissionRoot),

    #  * /submission/<ID>/status U3
    (r'/submission/' + submission_id_regexp + '/status',
                     submission.SubmissionStatus),

    #  * /submission/<ID>/finalize U4
    (r'/submission/' + submission_id_regexp + '/finalize',
                     submission.SubmissionFinalize),

    #  * /submission/<ID>/files U5
    (r'/submission/' + submission_id_regexp + '/files',
                     submission.SubmissionFiles),
    # https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    ## Tip Handlers ##
    #  * /tip/<ID>/ T1
    (r'/tip/' + tip_regexp, tip.TipRoot),

    #  * /tip/<ID>/comment T2
    (r'/tip/' + tip_regexp + '/comment',
                     tip.TipComment),

    #  * /tip/<ID>/files T3
    (r'/tip/' + tip_regexp + '/files',
                     tip.TipFiles),

    #  * /tip/<ID>/finalize T4
    (r'/tip/' + tip_regexp + '/finalize',
                     tip.TipFinalize),

    #  * /tip/<ID>/download T5
    (r'/tip/' + tip_regexp + '/download',
                     tip.TipDownload),

    #  * /tip/<ID>/pertinence T6
    (r'/tip/' + tip_regexp + '/pertinence',
                     tip.TipPertinence),

    ## Receiver Handlers ##
    #  * /reciever/<ID>/ R1
    (r'/receiver/' + tip_regexp, receiver.ReceiverRoot),

    #  * /receiver/<TIP ID>/<user moduletype> R2
    (r'/receiver/' + tip_regexp + '/' + user_module_regexp,
                     receiver.ReceiverModule),

    ## Admin Handlers ##
    #  * /admin/node A1
    (r'/admin/node', admin.AdminNode),

    #  * /admin/contexts A2
    (r'/admin/contexts/' + context_id_regexp,
                        admin.AdminContexts),

    #  * /admin/receivers/<context_ID> A3
    (r'/admin/receivers/' + context_id_regexp,
                    admin.AdminReceivers),

    #  * /admin/modules/<context_ID>/<MODULE TYPE> A4
    (r'/admin/modules/' + context_id_regexp + '/' + admin_module_regexp,
                    admin.AdminModules),

    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.glbackend.glclient_path})
]

