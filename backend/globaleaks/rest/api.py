# -*- coding: UTF-8
#   API
#   ***
#
#   This file contains the URI mapping for the GlobaLeaks API.

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSetting
from globaleaks.handlers import node, submission, rtip, wbtip, receiver, \
                                files, authentication, admstaticfiles, statistics,\
                                admlangfiles, overview, collection, wizard
from globaleaks.handlers import admin
from globaleaks.handlers.base import BaseStaticFileHandler, BaseRedirectHandler

uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
field_regexp = uuid_regexp

# Here is created the mapping betweehn urls and the associated handler.
#
# Most of th handlers conform to the following rules:
#
# * Create class: POST
#     manages the creation of a single resource
#
# * Instance: GET, PUT, DELETE, GET
#     manages the get, the update and the deletion of a single resource
#
# * Collection: GET
#    manages the get of a collection of resources

spec = [
    ## Authentication Handler ##
    (r'/authentication', authentication.AuthenticationHandler),

    ## Main Public Handlers ##
    (r'/node', node.NodeInstance),
    (r'/contexts', node.ContextsCollection),
    (r'/receivers' , node.ReceiversCollection),

    # Fake file hosting the Ahmia.fi descriptor
    (r'/description.json', node.AhmiaDescriptionHandler),

    ## Submission Handlers ##
    (r'/submission', submission.SubmissionCreate),
    (r'/submission/' + uuid_regexp, submission.SubmissionInstance),
    (r'/submission/' + uuid_regexp + '/file', files.FileInstance),

    ## Receiver Tip Handlers ##
    (r'/rtip/' + uuid_regexp, rtip.RTipInstance),
    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),
    (r'/rtip/' + uuid_regexp + r'/receivers', rtip.RTipReceiversCollection),
    (r'/rtip/' + uuid_regexp + '/download/' + uuid_regexp, files.Download),
    (r'/rtip/' + uuid_regexp + '/collection(?:/(zipstored|zipdeflated|tar|targz|tarbz2))?',
            collection.CollectionDownload),
    (r'/rtip/' + uuid_regexp + '/messages', rtip.ReceiverMsgCollection),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/wbtip/receivers', wbtip.WBTipReceiversCollection),
    (r'/wbtip/upload', files.FileAdd),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),

    ## Receiver Handlers ##
    (r'/receiver/preferences', receiver.ReceiverInstance),
    (r'/receiver/tips', receiver.TipsCollection),
    (r'/receiver/notifications', receiver.NotificationCollection),

    ## Admin Handlers ##
    (r'/admin/node', admin.NodeInstance),
    (r'/admin/contexts', admin.ContextsCollection),
    (r'/admin/context', admin.ContextCreate),
    (r'/admin/context/' + uuid_regexp, admin.ContextInstance),
    (r'/admin/receivers', admin.ReceiversCollection),
    (r'/admin/receiver', admin.ReceiverCreate),
    (r'/admin/receiver/' + uuid_regexp, admin.ReceiverInstance),
    (r'/admin/notification', admin.notification.NotificationInstance),
    (r'/admin/fields', admin.field.FieldsCollection),
    (r'/admin/field', admin.field.FieldCreate),
    (r'/admin/field/' + uuid_regexp, admin.field.FieldInstance),
    (r'/admin/fieldtemplates', admin.field.FieldTemplatesCollection),
    (r'/admin/fieldtemplate', admin.field.FieldTemplateCreate),
    (r'/admin/fieldtemplate/' + field_regexp, admin.field.FieldTemplateInstance),
    (r'/admin/anomalies', statistics.AnomaliesCollection),
    (r'/admin/stats/(\d+)', statistics.StatsCollection),
    (r'/admin/activities/(\w+)', statistics.RecentEventsCollection),
    (r'/admin/history', statistics.AnomalyHistoryCollection),
    (r'/admin/wizard', wizard.FirstSetup),
    (r'/admin/staticfiles', admstaticfiles.StaticFileList),
    (r'/admin/staticfiles/(.*)', admstaticfiles.StaticFileInstance,
            {'path': GLSetting.static_path}),
    (r'/admin/overview/tips', overview.Tips),
    (r'/admin/overview/users', overview.Users),
    (r'/admin/overview/files', overview.Files),

    ## Special Files Handlers##
    (r'/(favicon.ico)', BaseStaticFileHandler, {'path': GLSetting.static_path}),
    (r'/(robots.txt)', BaseStaticFileHandler, {'path': GLSetting.static_path}),
    (r'/static/(.*)', BaseStaticFileHandler, {'path': GLSetting.static_path}),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json',
            admlangfiles.LanguageFileHandler, {'path': GLSetting.static_path}),
    (r'/(.*)', BaseStaticFileHandler,
            {'path': GLSetting.glclient_path, 'default_filename': "index.html"}),

    ## Some Useful Redirects ##
    (r'/login', BaseRedirectHandler, {'url': '/#/login'}),
    (r'/admin', BaseRedirectHandler, {'url': '/#/admin'})
]
