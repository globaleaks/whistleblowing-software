# -*- coding: UTF-8
#   api
#   ***
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSetting
from globaleaks.handlers import node, submission, rtip, wbtip, admin, receiver, \
                                files, authentication, admstaticfiles, statistics,\
                                admlangfiles, overview, collection, wizard
from globaleaks.handlers.base import BaseStaticFileHandler, BaseRedirectHandler
from globaleaks.rest.requests import uuid_regexp

# Here is mapped a path and the associated class to be invoked,
# Two kind of Classes:
#
# * Instance
#         MAY supports: PUT, DELETE, GET
# * Collection
#         supports GET operation, returning a list of elements, and (maybe) POST
#         for create a new elements of the collection.
#
# [ special guest that do not respect this rule: SubmissionCreate ]

spec = [
    ## Node Handler ##
    (r'/node', node.InfoCollection),

    (r'/contexts', node.ContextsCollection),

    (r'/receivers' , node.ReceiversCollection),

    #  ahmia.fi integration with description.json file
    (r'/(description.json)', node.AhmiaDescriptionHandler),

    ## Submission Handlers ##
    (r'/submission', submission.SubmissionCreate),

    (r'/submission/' + uuid_regexp, submission.SubmissionInstance),

    (r'/submission/' + uuid_regexp + '/file', files.FileInstance),

    (r'/authentication', authentication.AuthenticationHandler),

    ## Receiver Tip Handlers ##

    (r'/rtip/' + uuid_regexp, rtip.RTipInstance),

    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),

    (r'/rtip/' + uuid_regexp + r'/receivers', rtip.RTipReceiversCollection),

    #  (Download a single file)
    (r'/rtip/' + uuid_regexp + '/download/' + uuid_regexp, files.Download),

    #  (Download all the file in various archive formats)
    (r'/rtip/' + uuid_regexp + '/collection(?:/(zipstored|zipdeflated|tar|targz|tarbz2))?', collection.CollectionDownload),

    (r'/rtip/' + uuid_regexp + '/messages', rtip.ReceiverMsgCollection),

    ## Whistleblower Tip Handlers

    (r'/wbtip', wbtip.WBTipInstance),

    (r'/wbtip/comments', wbtip.WBTipCommentCollection),

    (r'/wbtip/receivers', wbtip.WBTipReceiversCollection),

    (r'/wbtip/upload', files.FileAdd),

    #  W5 interaction with a single receiver
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),

    ## Receiver Handlers ##

    (r'/receiver/preferences', receiver.ReceiverInstance),

    (r'/receiver/tips', receiver.TipsCollection),

    ## Admin Handlers ##
    (r'/admin/node', admin.NodeInstance),
    (r'/admin/context', admin.ContextsCollection),
    (r'/admin/context/' + uuid_regexp, admin.ContextInstance),
    (r'/admin/receiver', admin.ReceiversCollection),
    (r'/admin/receiver/' + uuid_regexp, admin.ReceiverInstance),
    (r'/admin/notification', admin.NotificationInstance),

    (r'/admin/anomalies', statistics.AnomaliesCollection),
    (r'/admin/stats', statistics.StatsCollection),

    (r'/admin/wizard', wizard.FirstSetup),

    (r'/admin/appdata', wizard.AppdataCollection),
    # (r'/admin/templates', wizard.TemplateCollection),

    (r'/admin/staticfiles', admstaticfiles.StaticFileList),
    (r'/admin/staticfiles/(.*)', admstaticfiles.StaticFileInstance, {'path': GLSetting.static_path }),

    (r'/admin/overview/tips', overview.Tips),
    (r'/admin/overview/users', overview.Users),
    (r'/admin/overview/files', overview.Files),

]

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

## Special files (l10n/$lang.json)

spec.append(
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json', admlangfiles.LanguageFileHandler, {
        'path': GLSetting.static_path
    })
)

## Main Web app ##
# * /
spec.append(
    (r'/(.*)', BaseStaticFileHandler,
        {'path': GLSetting.glclient_path, 'default_filename': "index.html" }
    )
)

