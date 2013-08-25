# -*- coding: UTF-8
#   api
#   ***
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.

import os

from globaleaks.settings import GLSetting
from globaleaks.handlers import node, submission, tip, admin, receiver, files, authentication, admstaticfiles, overview
from globaleaks.handlers.base import BaseStaticFileHandler, BaseRedirectHandler
from globaleaks.rest.base import uuid_regexp


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
    (r'/authentication', authentication.AuthenticationHandler),

    ## Tip Handlers ##

    #  T1
    (r'/tip/' + uuid_regexp, tip.TipInstance),

    #  T2
    (r'/tip/' + uuid_regexp + r'/comments', tip.TipCommentCollection),

    #  T3
    (r'/tip/' + uuid_regexp + r'/receivers', tip.TipReceiversCollection),

    #  T4 = only the whistlebower can access to this interface, then the regexp match properly
    (r'/tip/' + uuid_regexp + r'/upload', files.FileAdd),

    #  T5 = only Receiver, download the files
    (r'/tip/' + uuid_regexp + '/download/' + uuid_regexp, files.Download),

    ## Receiver Handlers ##
    #  R1
    (r'/receiver/preferences', receiver.ReceiverInstance),

    #  R5
    (r'/receiver/tips', receiver.TipsCollection),

    ## Admin Handlers ##
    #  A1
    (r'/admin/node', admin.NodeInstance),

    #  A2
    (r'/admin/context', admin.ContextsCollection),

    #  A3
    (r'/admin/context/' + uuid_regexp, admin.ContextInstance),

    #  A4
    (r'/admin/receiver', admin.ReceiversCollection),

    #  A5
    (r'/admin/receiver/' + uuid_regexp, admin.ReceiverInstance),

    #  A6
    (r'/admin/notification', admin.NotificationInstance),

    #  A7
    (r'/admin/staticfiles', admstaticfiles.StaticFileCollection),

    #  A8
    (r'/admin/staticfiles/' + GLSetting.staticfile_regexp, admstaticfiles.StaticFileInstance),

    #  A9
    (r'/admin/overview/tips', overview.Tips),

    #  AA
    (r'/admin/overview/users', overview.Users),

    #  AB
    (r'/admin/overview/files', overview.Files),
]

## Enable end to end testing directory ##
# * /test
if GLSetting.cyclone_debug:
    spec.append(
        (r'/test/(.*)', BaseStaticFileHandler, {'path': os.path.join(GLSetting.glclient_path, '..', 'test')})
    )

## Utility redirect,
spec.append(
    (r'/login', BaseRedirectHandler, {'url': '/#/login'} )
)

## Static files services (would remain also if Client is not served by Backend)
spec.append(
    (r'/(favicon.ico)', BaseStaticFileHandler, {'path': GLSetting.static_path })
)

spec.append(
    (r'/(robots.txt)', BaseStaticFileHandler, {'path': GLSetting.static_path })
)

spec.append(
    (r'/static/(.*)', BaseStaticFileHandler, {'path': GLSetting.static_path })
)

## Main Web app ##
# * /
spec.append(
    (r'/(.*)', BaseStaticFileHandler,
        {'path': GLSetting.glclient_path, 'default_filename': "index.html" }
    )
)

