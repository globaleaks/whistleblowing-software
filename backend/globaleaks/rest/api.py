# -*- coding: UTF-8
#   API
#   ***
#
#   This file defines the URI mapping for the GlobaLeaks API and its factory
from cyclone import web

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.rest import requests
from globaleaks.settings import GLSettings
from globaleaks.handlers import exception, \
                                node, \
                                admin, receiver, custodian, \
                                submission, \
                                rtip, wbtip, \
                                files, authentication, token, \
                                export, langfiles, wizard, \
                                base, user, css, shorturl

from globaleaks.handlers.admin import node as admin_node
from globaleaks.handlers.admin import user as admin_user
from globaleaks.handlers.admin import receiver as admin_receiver
from globaleaks.handlers.admin import context as admin_context
from globaleaks.handlers.admin import step as admin_step
from globaleaks.handlers.admin import field as admin_field
from globaleaks.handlers.admin import langfiles as admin_langfiles
from globaleaks.handlers.admin import staticfiles as admin_staticfiles
from globaleaks.handlers.admin import overview as admin_overview
from globaleaks.handlers.admin import shorturl as admin_shorturl
from globaleaks.handlers.admin import statistics as admin_statistics
from globaleaks.handlers.admin import notification as admin_notification

from globaleaks.utils.utility import randbits

uuid_regexp      = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
shorturl_regexp  = r'(\/s\/[a-z0-9]{1,30})'
longurl_regexp   = r'(\/[a-z0-9=_\-%?\[\]\'\"]{0,255})'

spec = [
    (r'/exception', exception.ExceptionHandler),

    ## Some Useful Redirects ##
    (r'/login', base.BaseRedirectHandler, {'url': '/#/login'}),
    (r'/admin', base.BaseRedirectHandler, {'url': '/#/admin'}),
    (r'/custodian', base.BaseRedirectHandler, {'url': '/#/custodian'}),


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
    (r'/token/' + requests.token_regexp, token.TokenInstance),

    # Shorturl Handler
    (requests.shorturl_regexp, shorturl.ShortUrlInstance),

    ## Submission Handlers ##
    (r'/submission/' + requests.token_regexp, submission.SubmissionInstance),
    (r'/submission/' + requests.token_regexp + r'/file', files.FileInstance),

    ## Receiver Tip Handlers ##
    (r'/rtip/' + uuid_regexp, rtip.RTipInstance),
    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),
    (r'/rtip/' + uuid_regexp + r'/messages', rtip.ReceiverMsgCollection),
    (r'/rtip/' + uuid_regexp + r'/identityaccessrequests', rtip.IdentityAccessRequestsCollection),
    (r'/rtip/' + uuid_regexp + r'/receivers', rtip.RTipReceiversCollection),
    (r'/rtip/' + uuid_regexp + r'/download/' + uuid_regexp, files.Download),
    (r'/rtip/' + uuid_regexp + r'/export', export.ExportHandler),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/wbtip/receivers', wbtip.WBTipReceiversCollection),
    (r'/wbtip/upload', files.FileAdd),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),
    (r'/wbtip/' + uuid_regexp + r'/provideidentityinformation', wbtip.WBTipIdentityHandler),

    ## Receiver Handlers ##
    (r'/receiver/preferences', receiver.ReceiverInstance),
    (r'/receiver/tips', receiver.TipsCollection),
    (r'/rtip/operations', receiver.TipsOperations),

    (r'/custodian/identityaccessrequests', custodian.IdentityAccessRequestsCollection),
    (r'/custodian/identityaccessrequest/' + uuid_regexp, custodian.IdentityAccessRequestInstance),

    ## Admin Handlers ##
    (r'/admin/node', admin_node.NodeInstance),
    (r'/admin/users', admin_user.UsersCollection),
    (r'/admin/users/' + uuid_regexp, admin_user.UserInstance),
    (r'/admin/contexts', admin_context.ContextsCollection),
    (r'/admin/contexts/' + uuid_regexp, admin_context.ContextInstance),
    (r'/admin/receivers', admin_receiver.ReceiversCollection),
    (r'/admin/receivers/' + uuid_regexp, admin_receiver.ReceiverInstance),
    (r'/admin/notification', admin_notification.NotificationInstance),
    (r'/admin/fields', admin_field.FieldCollection),
    (r'/admin/fields/' + uuid_regexp, admin_field.FieldInstance),
    (r'/admin/steps', admin_step.StepCollection),
    (r'/admin/steps/' + uuid_regexp, admin_step.StepInstance),
    (r'/admin/fieldtemplates', admin_field.FieldTemplatesCollection),
    (r'/admin/fieldtemplates/' + uuid_regexp, admin_field.FieldTemplateInstance),
    (r'/admin/shorturls', admin_shorturl.ShortURLCollection),
    (r'/admin/shorturls/' + uuid_regexp, admin_shorturl.ShortURLInstance),
    (r'/admin/anomalies', admin_statistics.AnomaliesCollection),
    (r'/admin/stats/(\d+)', admin_statistics.StatsCollection),
    (r'/admin/activities/(summary|details)', admin_statistics.RecentEventsCollection),
    (r'/admin/history', admin_statistics.AnomalyHistoryCollection),
    (r'/admin/staticfiles', admin_staticfiles.StaticFileList),
    (r'/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json',
            admin_langfiles.AdminLanguageFileHandler),
    (r'/admin/staticfiles/([a-zA-Z0-9_\-\/\.]*)', admin_staticfiles.StaticFileInstance),
    (r'/admin/overview/tips', admin_overview.Tips),
    (r'/admin/overview/users', admin_overview.Users),
    (r'/admin/overview/files', admin_overview.Files),
    (r'/admin/wizard', wizard.FirstSetup),

    ## Special Files Handlers##
    (r'/(favicon.ico)', base.BaseStaticFileHandler),
    (r'/(robots.txt)', base.BaseStaticFileHandler),
    (r'/static/(.*)', base.BaseStaticFileHandler),
    (r'/css/styles.css', css.CSSFileHandler),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ').json',
            langfiles.LanguageFileHandler, {'path': GLSettings.client_path}),

    (r'/s/timingstats', base.TimingStatsHandler),

    ## This Handler should remain the last one as it works like a last resort catch 'em all
    (r'/([a-zA-Z0-9_\-\/\.]*)', base.BaseStaticFileHandler, {'path': GLSettings.client_path})
]

def get_api_factory():
    settings = dict(cookie_secret=randbits(128),
                    debug=GLSettings.log_requests_responses,
                    gzip=True)

    GLAPIFactory = web.Application(spec, **settings)
    GLAPIFactory.protocol = base.GLHTTPConnection

    return GLAPIFactory
