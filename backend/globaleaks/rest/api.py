# -*- coding: UTF-8
#   API
#   ***
#
#   This file defines the URI mapping for the GlobaLeaks API and its factory
from twisted.application import internet
from cyclone import web

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSettings
from globaleaks.handlers import exception, \
                                node, \
                                admin, receiver, custodian, \
                                submission, \
                                rtip, wbtip, \
                                files, authentication, admin, token, \
                                collection, langfiles, css, wizard, \
                                base, user

from globaleaks.handlers.admin.node import *
from globaleaks.handlers.admin.receiver import *
from globaleaks.handlers.admin.context import *
from globaleaks.handlers.admin.step import *
from globaleaks.handlers.admin.field import *
from globaleaks.handlers.admin.langfiles import *
from globaleaks.handlers.admin.staticfiles import *
from globaleaks.handlers.admin.overview import *
from globaleaks.handlers.admin.statistics import *
from globaleaks.handlers.admin.notification import *

from globaleaks.utils.utility import randbits

uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
field_regexp = uuid_regexp
token_string = r'([a-zA-Z0-9]{42})'

# Here is created the mapping between urls and the associated handler.
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
    (r'/exception', exception.ExceptionHandler),

    ## Some Useful Redirects ##
    (r'/login', base.BaseRedirectHandler, {'url': '/#/login'}),
    (r'/admin', base.BaseRedirectHandler, {'url': '/#/admin'}),

    ## Authentication Handlers ##
    (r'/authentication', authentication.AuthenticationHandler),
    (r'/receiptauth', authentication.ReceiptAuthHandler),

    ## Main Public Handlers ##
    (r'/node', node.NodeInstance),
    (r'/contexts', node.ContextsCollection),
    (r'/receivers' , node.ReceiversCollection),

    # Fake file hosting the Ahmia.fi descriptor
    (r'/description.json', node.AhmiaDescriptionHandler),

    # User Preferences Handler
    (r'/preferences', user.UserInstance),

    ## Token Handlers ##
    (r'/token', token.TokenCreate),
    (r'/token/' + token_string, token.TokenInstance),

    ## Submission Handlers ##
    (r'/submission/' + token_string, submission.SubmissionInstance),
    (r'/submission/' + token_string + '/file', files.FileInstance),

    ## Receiver Tip Handlers ##
    (r'/rtip/' + uuid_regexp, rtip.RTipInstance),
    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),
    (r'/rtip/' + uuid_regexp + '/messages', rtip.ReceiverMsgCollection),
    (r'/rtip/' + uuid_regexp + '/identityaccessrequests', rtip.IdentityAccessRequestsCollection),
    (r'/rtip/' + uuid_regexp + r'/receivers', rtip.RTipReceiversCollection),
    (r'/rtip/' + uuid_regexp + '/download/' + uuid_regexp, files.Download),
    (r'/rtip/' + uuid_regexp + '/collection', collection.CollectionDownload),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/wbtip/receivers', wbtip.WBTipReceiversCollection),
    (r'/wbtip/upload', files.FileAdd),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),

    ## Receiver Handlers ##
    (r'/receiver/preferences', receiver.ReceiverInstance),
    (r'/receiver/tips', receiver.TipsCollection),
    (r'/rtip/operations', receiver.TipsOperations),

    (r'/custodian/identityaccessrequests', custodian.IdentityAccessRequestsCollection),

    ## Admin Handlers ##
    (r'/admin/node', admin.node.NodeInstance),
    (r'/admin/users', admin.user.UsersCollection),
    (r'/admin/user', admin.user.UserCreate),
    (r'/admin/user/' + uuid_regexp, admin.user.UserInstance),
    (r'/admin/contexts', admin.context.ContextsCollection),
    (r'/admin/context', admin.context.ContextCreate),
    (r'/admin/context/' + uuid_regexp, admin.context.ContextInstance),
    (r'/admin/receivers', admin.receiver.ReceiversCollection),
    (r'/admin/receiver', admin.receiver.ReceiverCreate),
    (r'/admin/receiver/' + uuid_regexp, admin.receiver.ReceiverInstance),
    (r'/admin/notification', admin.notification.NotificationInstance),
    (r'/admin/field', admin.field.FieldCreate),
    (r'/admin/field/' + uuid_regexp, admin.field.FieldInstance),
    (r'/admin/step', admin.step.StepCreate),
    (r'/admin/step/' + uuid_regexp, admin.step.StepInstance),
    (r'/admin/fieldtemplates', admin.field.FieldTemplatesCollection),
    (r'/admin/fieldtemplate', admin.field.FieldTemplateCreate),
    (r'/admin/fieldtemplate/' + field_regexp, admin.field.FieldTemplateInstance),
    (r'/admin/anomalies', admin.statistics.AnomaliesCollection),
    (r'/admin/stats/(\d+)', admin.statistics.StatsCollection),
    (r'/admin/activities/(summary|details)', admin.statistics.RecentEventsCollection),
    (r'/admin/history', admin.statistics.AnomalyHistoryCollection),
    (r'/admin/staticfiles', admin.staticfiles.StaticFileList),
    (r'/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json',
            admin.langfiles.AdminLanguageFileHandler),
    (r'/admin/staticfiles/([a-zA-Z0-9_\-\/\.]*)', admin.staticfiles.StaticFileInstance),
    (r'/admin/overview/tips', admin.overview.Tips),
    (r'/admin/overview/users', admin.overview.Users),
    (r'/admin/overview/files', admin.overview.Files),
    (r'/admin/wizard', wizard.FirstSetup),

    ## Special Files Handlers##
    (r'/(favicon.ico)', base.BaseStaticFileHandler),
    (r'/(robots.txt)', base.BaseStaticFileHandler),
    (r'/static/(.*)', base.BaseStaticFileHandler),
    (r'/styles.css', css.LTRCSSFileHandler),
    (r'/styles-rtl.css', css.RTLCSSFileHandler),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json',
            langfiles.LanguageFileHandler, {'path': GLSettings.glclient_path}),

    (r'/s/timingstats', base.TimingStatsHandler),

    ## This Handler should remain the last one as it works like a last resort catch 'em all
    (r'/([a-zA-Z0-9_\-\/\.]*)', base.BaseStaticFileHandler, {'path': GLSettings.glclient_path})
]

def get_api_factory():
    settings = dict(cookie_secret=randbits(128),
                    debug=GLSettings.log_requests_responses,
                    gzip=True)

    GLAPIFactory = web.Application(spec, **settings)
    GLAPIFactory.protocol = base.GLHTTPConnection

    return GLAPIFactory
