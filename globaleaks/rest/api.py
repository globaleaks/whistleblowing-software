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
from globaleaks.handlers import node, submission, tip, admin, receiver, files
from globaleaks.rest.base import tipGUS, contextGUS, receiverGUS, profileGUS

tip_access_token = r'(\w+)' # XXX need to be changed with regexp.submission_gus | regexp.receipt_gus
not_defined_regexp = r'(\w+)'
receiver_token_auth = r'(\w+)' # This would cover regexp.tip_gus | regexp.welcome_token_gus

# Here is mapped a path and the associated class to be invoked,
# Three kind of Classes can be distigued:
#
# * Instance
#         MAY supports: PUT, DELETE, GET
# * Collection
#         supports GET operation, returning a list of elements, and (maybe) POST
#         for create a new elements of the collection.

spec = [
    ## Node Handler ##
    #  U1
    (r'/node', node.InfoCollection),

    ## Submission Handlers ##
    #  U2
    (r'/submission/' + contextGUS.regexp + '/new', submission.SubmissionInstance),

    #  U3
    (r'/file/', files.FileInstance),

    #  U4
    (r'/statistics', node.StatsCollection),

    #  U5
    (r'/contexts', node.ContextsCollection),

    #  U6
    (r'/receivers' , node.ReceiversCollection),

    ## Tip Handlers ##
    #  T1
    (r'/tip/' + tip_access_token, tip.TipInstance),

    #  T2
    (r'/tip/' + tip_access_token + r'/comments', tip.TipCommentCollection),

    #  T3
    (r'/tip/' + tip_access_token + r'/receivers', tip.TipReceiversCollection),

    ## Receiver Handlers ##
    #  R1
    (r'/receiver/' + receiver_token_auth + '/settings', receiver.ReceiverInstance),

    #  R2
    (r'/receiver/' + receiver_token_auth + '/profile', receiver.ProfilesCollection),

    #  R3
    (r'/receiver/' + receiver_token_auth + '/profile/' + profileGUS.regexp, receiver.ProfileInstance),

    #  R4
    (r'/receiver/' + receiver_token_auth + '/tip', tip.TipsCollection),

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
    (r'/admin/plugin/' + not_defined_regexp + r'/profile', admin.ProfileCollection),

    #  A8
    (r'/admin/plugin/' + not_defined_regexp + r'/profile/' + profileGUS.regexp, admin.ProfileInstance),

    #  A9
    (r'/admin/statistics/', admin.StatisticsCollection),

    ## Main Web app ##
    # * /
    (r'/(.*)', StaticFileHandler, {'path': config.main.glclient_path} ),

    #  -------------- ADMIN DEBUG ONLY -------------------
    #  AA
    (r'/admin/overview/' + not_defined_regexp, admin.EntryCollection),

    #  AB
    (r'/admin/tasks/' + not_defined_regexp, admin.TaskInstance)

]

