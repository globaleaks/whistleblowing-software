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
from globaleaks.messages.base import tipGUS, receiverGUS, submissionGUS, contextGUS, moduleENUM


more_lax = r'(\w+)' # XXX need to be changed with regexp.submission_id | regexp.receipt_id

spec = [
    ## Node Handler ##
    #  * /node U1
    (r'/node', node.PublicInfo),

    ## Submission Handlers ##
    #  * /submission/<context_GUS> U2
    (r'/submission/' + contextGUS.regexp + '/new', submission.SubmissionRoot),

    #  * /submission/<GUS>/status U3
    (r'/submission/' + submissionGUS.regexp + '/status', submission.SubmissionStatus),

    #  * /submission/<GUS>/finalize U4
    (r'/submission/' + submissionGUS.regexp + '/finalize', submission.SubmissionFinalize),

    (r'/submission/' + submissionGUS.regexp + '/files', files.FilesHandler),
    # https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    ## Tip Handlers ##
    #  * /tip/<tip_GUS>/ T1
    (r'/tip/' + more_lax, tip.TipRoot),

    #  * /tip/<tip_GUS>/comment T2
    (r'/tip/' + tipGUS.regexp + '/comment', tip.TipComment),

    #  * /tip/<tip_GUS>/files T3
    (r'/tip/' + tipGUS.regexp + '/files', tip.TipFiles),

    #  * /tip/<tip_GUS>/finalize T4
    (r'/tip/' + tipGUS.regexp + '/finalize', tip.TipFinalize),

    #  * /tip/<tip_GUS>/download T5
    (r'/tip/' + tipGUS.regexp + '/download', tip.TipDownload),

    #  * /tip/<tip_GUS>/pertinence T6
    (r'/tip/' + tipGUS.regexp + '/pertinence', tip.TipPertinence),

    ## Receiver Handlers ##
    #  * /reciever/<tip_GUS>/ R1
    (r'/receiver/' + tipGUS.regexp, receiver.ReceiverRoot),

    #  * /receiver/<tip_GUS>/<user moduletype> R2
    (r'/receiver/' + tipGUS.regexp + '/' + moduleENUM.regexp, receiver.ReceiverModule),

    ## Admin Handlers ##
    #  * /admin/node A1
    (r'/admin/node', admin.AdminNode),

    #  * /admin/contexts A2
    (r'/admin/contexts/' + contextGUS.regexp, admin.AdminContexts),

    #  * /admin/receivers/<receiver_GUS> A3
    (r'/admin/receivers/' + receiverGUS.regexp, admin.AdminReceivers),

    #  * /admin/modules/<context_GUS>/<MODULE TYPE> A4
    (r'/admin/modules/' + contextGUS.regexp + '/' + moduleENUM.regexp, admin.AdminModules),

    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.main.glclient_path})
]

