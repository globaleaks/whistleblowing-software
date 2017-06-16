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
from twisted.python.failure import Failure

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

from globaleaks.rest import apicache, requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import randbits
from globaleaks.utils.mailutils import extract_exception_traceback_and_send_email


uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'

api_spec = [
    (r'/exception', exception.ExceptionHandler),

    ## Authentication Handlers ##
    (r'/authentication', authentication.AuthenticationHandler),
    (r'/receiptauth', authentication.ReceiptAuthHandler),
    (r'/session', authentication.SessionHandler),

    ## Public API ##
    (r'/public', public.PublicResource),

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
    (r'/rtip/' + uuid_regexp + r'/export', export.ExportHandler),
    (r'/rtip/' + uuid_regexp + r'/wbfile', rtip.WhistleblowerFileHandler),
    (r'/rtip/rfile/' + uuid_regexp, rtip.ReceiverFileDownload),
    (r'/rtip/wbfile/' + uuid_regexp, rtip.RTipWBFileInstanceHandler),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),
    (r'/wbtip/rfile', files.FileAdd),
    (r'/wbtip/wbfile/' + uuid_regexp, wbtip.WBTipWBFileInstanceHandler),
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
    (r'/admin/(users|contexts)/' + uuid_regexp  + r'/img', admin_modelimgs.ModelImgInstance),
    (r'/admin/questionnaires', admin_questionnaire.QuestionnairesCollection),
    (r'/admin/questionnaires/' + uuid_regexp, admin_questionnaire.QuestionnaireInstance),
    (r'/admin/receivers', admin_receiver.ReceiversCollection),
    (r'/admin/receivers/' + uuid_regexp, admin_receiver.ReceiverInstance),
    (r'/admin/notification', admin_notification.NotificationInstance),
    (r'/admin/notification/mail', admin_notification.NotificationTestInstance),
    (r'/admin/fields', admin_field.FieldCollection),
    (r'/admin/fields/' + uuid_regexp, admin_field.FieldInstance),
    (r'/admin/steps', admin_step.StepCollection),
    (r'/admin/steps/' + uuid_regexp, admin_step.StepInstance),
    (r'/admin/fieldtemplates', admin_field.FieldTemplatesCollection),
    (r'/admin/fieldtemplates/' + uuid_regexp, admin_field.FieldTemplateInstance),
    (r'/admin/shorturls', admin_shorturl.ShortURLCollection),
    (r'/admin/shorturls/' + uuid_regexp, admin_shorturl.ShortURLInstance),
    (r'/admin/stats/(\d+)', admin_statistics.StatsCollection),
    (r'/admin/activities/(summary|details)', admin_statistics.RecentEventsCollection),
    (r'/admin/anomalies', admin_statistics.AnomalyCollection),
    (r'/admin/jobs', admin_statistics.JobsTiming),
    (r'/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', admin_l10n.AdminL10NHandler),
    (r'/admin/files/(logo|favicon|css|homepage|script)', admin_files.FileInstance),
    (r'/admin/config/tls', https.ConfigHandler),
    (r'/admin/config/tls/hostname', https.HostnameTestHandler),
    (r'/admin/config/tls/files/(csr)', https.CSRFileHandler),
    (r'/admin/config/tls/files/(cert|chain|priv_key)', https.FileHandler),
    (r'/admin/staticfiles$', admin_staticfiles.StaticFileList),
    (r'/admin/staticfiles/(.+)', admin_staticfiles.StaticFileInstance),
    (r'/admin/overview/tips', admin_overview.Tips),
    (r'/admin/overview/files', admin_overview.Files),
    (r'/wizard', wizard.Wizard),

    (r'/admin/config/acme/run', https.AcmeHandler),
    (r'/.well-known/acme-challenge/([a-zA-Z0-9_\-]{42,44})', https.AcmeChallResolver),

    ## Special Files Handlers##
    (r'/robots.txt', robots.RobotstxtHandler),
    (r'/sitemap.xml', robots.SitemapHandler),
    (r'/s/(.+)', base.StaticFileHandler, {'path': GLSettings.static_path}),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', l10n.L10NHandler),

    ## This handler attempts to route all non routed get requests
    (r'/([a-zA-Z0-9_\-\/\.]*)', base.StaticFileHandler, {'path': GLSettings.client_path})
]


def decorate_method(h, method):
   decorator_authentication = getattr(h, 'authentication')
   value = getattr(h, 'check_roles')
   if type(value) is str:
       value = {value}

   f = getattr(h, method)

   if method == 'get':
       if h.cache_resource:
           f = apicache.decorator_cache_get(f)

   else:
       if h.invalidate_cache:
           f = apicache.decorator_cache_invalidate(f)

   f = decorator_authentication(f, value)

   setattr(h, method, f)


class APIResourceWrapper(Resource):
    _registry = None
    isLeaf = True

    def __init__(self):
        Resource.__init__(self)
        self._registry = []

        decorated_handlers = set()

        for tup in api_spec:
            args = {}
            if len(tup) == 2:
                pattern, handler = tup
            else:
                pattern, handler, args = tup

            if not pattern.startswith("^"):
                pattern = "^" + pattern;

            if not pattern.endswith("$"):
                pattern += "$"

            if handler not in decorated_handlers:
                decorated_handlers.add(handler)
                for m in ['get', 'put', 'post', 'delete']:
                    if hasattr(handler, m):
                        decorate_method(handler, m)

            self._registry.append((re.compile(pattern), handler, args))

    def handle_exception(self, e, request):
        """
        handle_exception is a callback that decorators all deferreds in render

        It responds to properly handled GL Exceptions by pushing the error msgs
        to the client and it spools a mail in the case the exception is unknown
        and unhandled.

        @param e: A `Twisted.python.Failure` instance that wraps a `GLException`
                  or a normal `Exception`
        @param request: The `twisted.web.Request`
        """
        if isinstance(e, errors.GLException):
            pass
        elif isinstance(e.value, errors.GLException):
            e = e.value
        else:
            # TODO(evilaliv3) defer extract_and_email
            extract_exception_traceback_and_send_email(e)
            e = errors.InternalServerError('Unexpected')

        request.setResponseCode(e.status_code)
        request.write({
            'error_message': e.reason,
            'error_code': e.error_code,
            'arguments': getattr(e, 'arguments', [])
        })

    def render(self, request):
        """
        @param request: `twisted.web.Request`

        @return: empty `str` or `NOT_DONE_YET`
        """

        self.set_default_headers(request)

        request_finished = [False]
        def _finish(_):
            request_finished[0] = True

        request.notifyFinish().addBoth(_finish)

        match = None
        for regexp, handler, args in self._registry:
            match = regexp.match(request.path)
            if match:
                break

        if match is None:
            self.handle_exception(errors.ResourceNotFound(), request)
            return b''

        method = request.method.lower()
        if not method in ['get', 'post', 'put', 'delete'] or not hasattr(handler, method):
            self.handle_exception(errors.MethodNotImplemented(), request)
            return b''

        f = getattr(handler, method)

        groups = [unicode(g) for g in match.groups()]
        h = handler(request, **args)
        d = defer.maybeDeferred(f, h, *groups)

        @defer.inlineCallbacks
        def concludeHandlerFailure(err):
            yield h.execution_check()

            self.handle_exception(err, request)

            if not request_finished[0]:
                request.finish()

        @defer.inlineCallbacks
        def concludeHandlerSuccess(ret):
            """Concludes successful execution of a `BaseHandler` instance

            @param ret: A `dict`, `str`, `None` or something unexpected
            """
            yield h.execution_check()

            if not ret is None:
                h.write(ret)

            if not request_finished[0]:
                request.finish()

        d.addErrback(concludeHandlerFailure)
        d.addCallback(concludeHandlerSuccess)
        return NOT_DONE_YET

    def render_GET(self, request):
        request.setReponseCode(200)
        return self.render(self, request)

    def render_PUT(self, request):
        request.setReponseCode(202)
        return self.render(self, request)

    def render_POST(self, request):
        request.setReponseCode(201)
        return self.render(self, request)

    @staticmethod
    def set_default_headers(request):
        # to avoid version attacks
        request.setHeader("Server", "Globaleaks")

        # to reduce possibility for XSS attacks.
        request.setHeader("X-Content-Type-Options", "nosniff")
        request.setHeader("X-XSS-Protection", "1; mode=block")

        # to disable caching
        request.setHeader("Cache-control", "no-cache, no-store, must-revalidate")
        request.setHeader("Pragma", "no-cache")
        request.setHeader("Expires", "-1")

        # to avoid information leakage via referrer
        request.setHeader("Referrer-Policy", "no-referrer")

        request.setHeader("Connection", "close")

        # to avoid Robots spidering, indexing, caching
        if not GLSettings.memory_copy.allow_indexing:
            request.setHeader("X-Robots-Tag", "noindex")

        # to mitigate clickjaking attacks on iframes allowing only same origin
        # same origin is needed in order to include svg and other html <object>
        if not GLSettings.memory_copy.allow_iframes_inclusion:
            request.setHeader("X-Frame-Options", "sameorigin")
