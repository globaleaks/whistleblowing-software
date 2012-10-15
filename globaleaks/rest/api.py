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

from cyclone.web import StaticFileHandler

from globaleaks import config
from globaleaks.handlers import node, submission, tip, admin, receiver, files
from globaleaks.messages.base import tipID, submissionID, contextID, moduleENUM


spec = [
    ## Node Handler ##
    #  * /node U1
    (r'/node', node.Node),

    ## Submission Handlers ##
    #  * /submission/ U2
    (r'/submission', submission.SubmissionRoot),

    #  * /submission/<ID>/status U3
    (r'/submission/' + submissionID.regexp + '/status', submission.SubmissionStatus),

    #  * /submission/<ID>/finalize U4
    (r'/submission/' + submissionID.regexp + '/finalize', submission.SubmissionFinalize),

    (r'/submission/' + submissionID.regexp + '/files', files.FilesHandler),
    # https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    ## Tip Handlers ##
    #  * /tip/<ID>/ T1
    (r'/tip/' + tipID.regexp, tip.TipRoot),

    #  * /tip/<ID>/comment T2
    (r'/tip/' + tipID.regexp + '/comment', tip.TipComment),

    #  * /tip/<ID>/files T3
    (r'/tip/' + tipID.regexp + '/files', tip.TipFiles),

    #  * /tip/<ID>/finalize T4
    (r'/tip/' + tipID.regexp + '/finalize', tip.TipFinalize),

    #  * /tip/<ID>/download T5
    (r'/tip/' + tipID.regexp + '/download', tip.TipDownload),

    #  * /tip/<ID>/pertinence T6
    (r'/tip/' + tipID.regexp + '/pertinence', tip.TipPertinence),

    ## Receiver Handlers ##
    #  * /reciever/<ID>/ R1
    (r'/receiver/' + tipID.regexp, receiver.ReceiverRoot),

    #  * /receiver/<TIP ID>/<user moduletype> R2
    (r'/receiver/' + tipID.regexp + '/' + moduleENUM.regexp, receiver.ReceiverModule),

    ## Admin Handlers ##
    #  * /admin/node A1
    (r'/admin/node', admin.AdminNode),

    #  * /admin/contexts A2
    (r'/admin/contexts/' + contextID.regexp, admin.AdminContexts),

    #  * /admin/receivers/<context_ID> A3
    (r'/admin/receivers/' + contextID.regexp, admin.AdminReceivers),

    #  * /admin/modules/<context_ID>/<MODULE TYPE> A4
    (r'/admin/modules/' + contextID.regexp + '/' + moduleENUM.regexp, admin.AdminModules),

    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.glbackend.glclient_path})
]

