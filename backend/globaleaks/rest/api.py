# -*- coding: UTF-8
#   API
#   ***
#
#   This file defines the URI mapping for the GlobaLeaks API and its factory

import re

from urlparse import parse_qs

from twisted.internet import reactor, defer
from twisted.web.resource import Resource, NoResource
from twisted.web.server import NOT_DONE_YET

from globaleaks import LANGUAGES_SUPPORTED_CODES

from globaleaks.handlers import exception, \
                                receiver, custodian, \
                                public, \
                                submission, \
                                rtip, wbtip, \
                                files, authentication, token, \
                                export, l10n, wizard, \
                                base, user, shorturl, \
                                robots

from globaleaks.handlers.admin import context as admin_context
from globaleaks.handlers.admin import field as admin_field
from globaleaks.handlers.admin import files as admin_files
from globaleaks.handlers.admin import https
from globaleaks.handlers.admin import l10n as admin_l10n
from globaleaks.handlers.admin import modelimgs as admin_modelimgs
from globaleaks.handlers.admin import node as admin_node
from globaleaks.handlers.admin import notification as admin_notification
from globaleaks.handlers.admin import overview as admin_overview
from globaleaks.handlers.admin import questionnaire as admin_questionnaire
from globaleaks.handlers.admin import receiver as admin_receiver
from globaleaks.handlers.admin import shorturl as admin_shorturl
from globaleaks.handlers.admin import staticfiles as admin_staticfiles
from globaleaks.handlers.admin import statistics as admin_statistics
from globaleaks.handlers.admin import step as admin_step
from globaleaks.handlers.admin import user as admin_user

from globaleaks.rest import requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import randbits


uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'

api_spec = [
    (r'/exception', exception.ExceptionHandler, None),

    ## Authentication Handlers ##
    (r'/authentication', authentication.AuthenticationHandler, None),
    (r'/receiptauth', authentication.ReceiptAuthHandler, None),
    (r'/session', authentication.SessionHandler, None),

    ## Public API ##
    (r'/public', public.PublicResource, None),

    # User Preferences Handler
    (r'/preferences', user.UserInstance, None),

    ## Token Handlers ##
    (r'/token', token.TokenCreate, None),
    (r'/token/' + requests.token_regexp, token.TokenInstance, None),

    # Shorturl Handler
    (requests.shorturl_regexp, shorturl.ShortUrlInstance, None),

    ## Submission Handlers ##
    (r'/submission/' + requests.token_regexp, submission.SubmissionInstance, None),
    (r'/submission/' + requests.token_regexp + r'/file', files.FileInstance, None),

    ## Receiver Tip Handlers ##
    (r'/rtip/' + uuid_regexp, rtip.RTipInstance, None),
    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection, None),
    (r'/rtip/' + uuid_regexp + r'/messages', rtip.ReceiverMsgCollection, None),
    (r'/rtip/' + uuid_regexp + r'/identityaccessrequests', rtip.IdentityAccessRequestsCollection, None),
    (r'/rtip/' + uuid_regexp + r'/export', export.ExportHandler, None),
    (r'/rtip/' + uuid_regexp + r'/wbfile', rtip.WhistleblowerFileHandler, None),
    (r'/rtip/rfile/' + uuid_regexp, rtip.ReceiverFileDownload, None),
    (r'/rtip/wbfile/' + uuid_regexp, rtip.RTipWBFileInstanceHandler, None),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance, None),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection, None),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection, None),
    (r'/wbtip/rfile', files.FileAdd, None),
    (r'/wbtip/wbfile/' + uuid_regexp, wbtip.WBTipWBFileInstanceHandler, None),
    (r'/wbtip/' + uuid_regexp + r'/provideidentityinformation', wbtip.WBTipIdentityHandler, None),

    ## Receiver Handlers ##
    (r'/receiver/preferences', receiver.ReceiverInstance, None),
    (r'/receiver/tips', receiver.TipsCollection, None),
    (r'/rtip/operations', receiver.TipsOperations, None),

    (r'/custodian/identityaccessrequests', custodian.IdentityAccessRequestsCollection, None),
    (r'/custodian/identityaccessrequest/' + uuid_regexp, custodian.IdentityAccessRequestInstance, None),

    ## Admin Handlers ##
    (r'/admin/node', admin_node.NodeInstance, None),
    (r'/admin/users', admin_user.UsersCollection, None),
    (r'/admin/users/' + uuid_regexp, admin_user.UserInstance, None),
    (r'/admin/contexts', admin_context.ContextsCollection, None),
    (r'/admin/contexts/' + uuid_regexp, admin_context.ContextInstance, None),
    (r'/admin/(users|contexts)/' + uuid_regexp  + r'/img', admin_modelimgs.ModelImgInstance, None),
    (r'/admin/questionnaires', admin_questionnaire.QuestionnairesCollection, None),
    (r'/admin/questionnaires/' + uuid_regexp, admin_questionnaire.QuestionnaireInstance, None),
    (r'/admin/receivers', admin_receiver.ReceiversCollection, None),
    (r'/admin/receivers/' + uuid_regexp, admin_receiver.ReceiverInstance, None),
    (r'/admin/notification', admin_notification.NotificationInstance, None),
    (r'/admin/notification/mail', admin_notification.NotificationTestInstance, None),
    (r'/admin/fields', admin_field.FieldCollection, None),
    (r'/admin/fields/' + uuid_regexp, admin_field.FieldInstance, None),
    (r'/admin/steps', admin_step.StepCollection, None),
    (r'/admin/steps/' + uuid_regexp, admin_step.StepInstance, None),
    (r'/admin/fieldtemplates', admin_field.FieldTemplatesCollection, None),
    (r'/admin/fieldtemplates/' + uuid_regexp, admin_field.FieldTemplateInstance, None),
    (r'/admin/shorturls', admin_shorturl.ShortURLCollection, None),
    (r'/admin/shorturls/' + uuid_regexp, admin_shorturl.ShortURLInstance, None),
    (r'/admin/stats/(\d+)', admin_statistics.StatsCollection, None),
    (r'/admin/activities/(summary|details)', admin_statistics.RecentEventsCollection, None),
    (r'/admin/anomalies', admin_statistics.AnomalyCollection, None),
    (r'/admin/jobs', admin_statistics.JobsTiming, None),
    (r'/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', admin_l10n.AdminL10NHandler, None),
    (r'/admin/files/(logo|favicon|css|homepage|script)', admin_files.FileInstance, None),
    (r'/admin/config/tls', https.ConfigHandler, None),
    (r'/admin/config/tls/files/(csr)', https.CSRFileHandler, None),
    (r'/admin/config/tls/files/(cert|chain|priv_key)', https.FileHandler, None),
    (r'/admin/staticfiles$', admin_staticfiles.StaticFileList, None),
    (r'/admin/staticfiles/(.+)', admin_staticfiles.StaticFileInstance, None),
    (r'/admin/overview/tips', admin_overview.Tips, None),
    (r'/admin/overview/files', admin_overview.Files, None),
    (r'/wizard', wizard.Wizard, None),

    ## Special Files Handlers##
    (r'/robots.txt', robots.RobotstxtHandler, None),
    (r'/sitemap.xml', robots.SitemapHandler, None),
    (r'/s/(.+)', base.StaticFileHandler, {'path': GLSettings.static_path}),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', l10n.L10NHandler, None),

    ## This Handler should remain the last one as it works like a last resort catch 'em all
    (r'/([a-zA-Z0-9_\-\/\.]*)', base.StaticFileHandler, {'path': GLSettings.client_path})
]

def decorate_method(h, method):
   decorator = getattr(h, 'authentication')
   value = getattr(h, 'check_roles')
   value = re.split("[ ,]", value)
   setattr(h, method, decorator(getattr(h, method), value))


class APIResourceWrapper(Resource):
    _registry = None
    isLeaf = True

    def __init__(self):
        Resource.__init__(self)
        self._registry = []

        for pattern, handler, args, in api_spec:
            if not pattern.startswith("^"):
                pattern = "^" + pattern;

            if not pattern.endswith("$"):
                pattern += "$"

            self._registry.append((re.compile(pattern), handler, args))

    def handle_exception(self, e, request):
        handle = False
        if isinstance(e, errors.GLException):
            handle = True
        elif isinstance(e.value, errors.GLException):
            e = e.value
            handle = True

        if handle:
            request.setResponseCode(e.status_code)

            error_dict = {
                'error_message': e.reason,
                'error_code': e.error_code
            }

            if hasattr(e, 'arguments'):
                error_dict.update({'arguments': e.arguments})
            else:
                error_dict.update({'arguments': []})

            request.write(error_dict)

    def render(self, request):
        request_finished = [False]

        def _finish(self):
            request_finished[0] = True

        request.notifyFinish().addBoth(_finish)

        for regexp, handler, args in self._registry:
            method = request.method.lower()

            if method not in ['get', 'post', 'put', 'delete']:
                continue

            match = regexp.match(request.path)
            if not match:
                continue

            if args is None:
                args = {}

            groups = [unicode(g) for g in match.groups()]

            h = handler(request, **args)

            if not hasattr(handler, method):
                self.handle_exception(errors.MethodNotImplemented(), request)
                return ''

            decorate_method(h, method)

            f = getattr(h, method)

            d = defer.maybeDeferred(f, *groups)

            @defer.inlineCallbacks
            def both(ret):
                yield h.execution_check()

                if ret is not None:
                    h.write(ret)

                if not request_finished[0]:
                   request.finish()

            d.addErrback(self.handle_exception, request)
            d.addBoth(both)
            return NOT_DONE_YET

        self.handle_exception(errors.ResourceNotFound(), request)

        return NOT_DONE_YET

    def render_GET(self, request):
        return self.render(self, request)

    def render_PUT(self, request):
        return self.render(self, request)

    def render_POST(self, request):
        return self.render(self, request)
