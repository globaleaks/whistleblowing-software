# -*- coding: UTF-8
#   api
#   ***
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.

import os

from cyclone.web import StaticFileHandler

from globaleaks import settings
from globaleaks.handlers import node, submission, tip, admin, receiver, files, debug, authentication
from globaleaks.rest.base import tipGUS, contextGUS, receiverGUS, submissionGUS, fileGUS, uuid_regexp

tip_access_token = r'(\w+)' # XXX need to be changed with regexp.submission_gus | regexp.receipt_gus
not_defined_regexp = r'(\w+)'
only_int_regexp = r'(\d+)'
receiver_token_auth = uuid_regexp
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
    (r'/submission/' + uuid_regexp, submission.SubmissionInstance),

    #  U4
    (r'/submission/' + uuid_regexp + '/file', files.FileInstance),

    #  U5
    (r'/statistics', node.StatsCollection),

    #  U6
    (r'/contexts', node.ContextsCollection),

    #  U7
    (r'/receivers' , node.ReceiversCollection),

    #  U8
    (r'/login', authentication.AuthenticationHandler),

    ## Tip Handlers ##

    #  T1
    (r'/tip/' + uuid_regexp, tip.TipInstance),

    #  T2
    (r'/tip/' + uuid_regexp + r'/comments', tip.TipCommentCollection),

    #  T3
    (r'/tip/' + uuid_regexp + r'/receivers', tip.TipReceiversCollection),

    #  T4 = only the whistlebower can access to this interface, then the regexp match properly
    (r'/tip/' + uuid_regexp + '/upload', files.FileInstance),

    #  T5 = only Receiver, download the files
    (r'/tip/' + uuid_regexp + '/download/' + fileGUS, files.Download),

    ## Receiver Handlers ##
    #  R1
    (r'/receiver/' + receiver_token_auth + '/settings', receiver.ReceiverInstance),

    #  R5
    (r'/receiver/' + receiver_token_auth + '/tip', receiver.TipsCollection),

    ## Admin Handlers ##
    #  A1
    (r'/admin/node', admin.NodeInstance),

    #  A2
    (r'/admin/context', admin.ContextsCollection),

    #  A3
    (r'/admin/context/' + uuid_regexp, admin.ContextInstance),

    #  A4
    (r'/admin/receiver', admin.ReceiversCollection),

    #  A5 receiverGUS
    (r'/admin/receiver/' + uuid_regexp, admin.ReceiverInstance),

    #  A6
    (r'/admin/plugin', admin.PluginCollection),

    #  AB
    (r'/admin/statistics/', admin.StatisticsCollection),

    #  D2
    (r'/debug/tasks/' + not_defined_regexp, debug.TaskInstance),

]

## Enable end to end testing directory ##
# * /test
#if settings.config.debug.testing:
spec.append(
    (r'/test/(.*)', StaticFileHandler, {'path': os.path.join(settings.glclient_path, '..', 'test')})
)

## Main Web app ##
# * /
spec.append(
    (r'/(.*)', StaticFileHandler, {'path': settings.glclient_path, 'default_filename': "index.html" } )
)

