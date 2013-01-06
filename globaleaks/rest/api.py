# -*- coding: UTF-8
#   api
#   ***
# 
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.

from cyclone.web import StaticFileHandler

from globaleaks import config
from globaleaks.handlers import node, submission, tip, admin, receiver, files, debug
from globaleaks.rest.base import tipGUS, contextGUS, receiverGUS, profileGUS, submissionGUS

tip_access_token = r'(\w+)' # XXX need to be changed with regexp.submission_gus | regexp.receipt_gus
not_defined_regexp = r'(\w+)'
receiver_token_auth = r'(\w+)' # This would cover regexp.tip_gus | regexp.welcome_token_gus
wb_receipt = r'(\w+)'

# Here is mapped a path and the associated class to be invoked,
# Two kind of Classes:
#
# * Instance
#         MAY supports: PUT, DELETE, GET
# * Collection
#         supports GET operation, returning a list of elements, and (maybe) POST
#         for create a new elements of the collection.
#
# [ special guest: SubmissionCreate, our lovely black sheep ;) ]

spec = [
    ## Node Handler ##
    #  U1
    (r'/node', node.InfoCollection),

    ## Submission Handlers ##
    #  U2
    (r'/submission', submission.SubmissionCreate),

    #  U3
    (r'/submission/' + submissionGUS.regexp, submission.SubmissionInstance),

    #  U4
    (r'/submission/' + submissionGUS.regexp + '/file', files.FileInstance),

    #  U5
    (r'/statistics', node.StatsCollection),

    #  U6
    (r'/contexts', node.ContextsCollection),

    #  U7
    (r'/receivers' , node.ReceiversCollection),

    ## Tip Handlers ##
    #  T1
    (r'/tip/' + tip_access_token, tip.TipInstance),

    #  T2
    (r'/tip/' + tip_access_token + r'/comments', tip.TipCommentCollection),

    #  T3
    (r'/tip/' + tip_access_token + r'/receivers', tip.TipReceiversCollection),

    #  T4 = only the whistlebower can access to this interface, then the regexp match properly
    (r'/tip/' + wb_receipt + '/file', files.FileInstance),

    ## Receiver Handlers ##
    #  R1
    (r'/receiver/' + receiver_token_auth + '/settings', receiver.ReceiverInstance),

    #  R2
    (r'/receiver/' + receiver_token_auth + '/profile', receiver.ProfilesCollection),

    #  R3
    (r'/receiver/' + receiver_token_auth + '/profile/' + profileGUS.regexp, receiver.ProfileInstance),

    #  R4
    (r'/receiver/' + receiver_token_auth + '/tip', receiver.TipsCollection),

    ## Admin Handlers ##
    #  A1
    (r'/admin/node', admin.NodeInstance),

    #  A2
    (r'/admin/context', admin.ContextsCollection),

    #  A3
    (r'/admin/context/' + contextGUS.regexp, admin.ContextInstance),

    #  A4
    (r'/admin/receiver', admin.ReceiversCollection),

    #  A5
    (r'/admin/receiver/' + receiverGUS.regexp, admin.ReceiverInstance),

    #  A6
    (r'/admin/plugin', admin.PluginCollection),

    #  A7
    (r'/admin/profile', admin.ProfileCollection),

    #  A8
    (r'/admin/profile/' + profileGUS.regexp, admin.ProfileInstance),

    #  A9
    (r'/admin/statistics/', admin.StatisticsCollection),

    #  D1
    (r'/debug/overview/' + not_defined_regexp, debug.EntryCollection),

    #  D2
    (r'/debug/tasks/' + not_defined_regexp, debug.TaskInstance),

    ## file download TEMP
    (r'/download/(.*)',  files.Download),  # StaticFileHandler, {'path': config.advanced.submissions_dir } ),

    ## Main Web app ##
    # * /
    (r'/(.*)', StaticFileHandler, {'path': config.main.glclient_path, 'default_filename': "index.html" } )
]

