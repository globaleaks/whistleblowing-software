# -*- coding: utf-8
#   API
#   ***
#
#   This file defines the URI mapping for the GlobaLeaks API and its factory
import inspect
import json
import re

from sqlalchemy.orm.exc import NoResultFound

from twisted.internet import defer
from twisted.internet.abstract import isIPAddress, isIPv6Address
from twisted.python.failure import Failure
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.handlers import custodian, \
                                email_validation, \
                                file, \
                                receiver, \
                                password_reset, \
                                public, \
                                submission, \
                                rtip, wbtip, \
                                attachment, authentication, token, \
                                export, l10n, wizard,\
                                user, \
                                redirect, \
                                robots, \
                                script, \
                                signup, \
                                sitemap, \
                                support, \
                                staticfile, \
                                security, \
                                viewer

from globaleaks.handlers.admin import context as admin_context
from globaleaks.handlers.admin import field as admin_field
from globaleaks.handlers.admin import file as admin_file
from globaleaks.handlers.admin import https
from globaleaks.handlers.admin import l10n as admin_l10n
from globaleaks.handlers.admin import node as admin_node
from globaleaks.handlers.admin import network as admin_network
from globaleaks.handlers.admin import notification as admin_notification
from globaleaks.handlers.admin import operation as admin_operation
from globaleaks.handlers.admin import questionnaire as admin_questionnaire
from globaleaks.handlers.admin import redirect as admin_redirect
from globaleaks.handlers.admin import auditlog as admin_auditlog
from globaleaks.handlers.admin import step as admin_step
from globaleaks.handlers.admin import tenant as admin_tenant
from globaleaks.handlers.admin import user as admin_user
from globaleaks.handlers.admin import submission_statuses as admin_submission_statuses

from globaleaks.rest import decorators, requests, errors
from globaleaks.state import State, extract_exception_traceback_and_schedule_email
from globaleaks.utils.json import JSONEncoder

tid_regexp = r'([0-9]+)'
uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
key_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|[a-z_]{0,100})'

api_spec = [
    # Authentication Handlers
    (r'/api/authentication', authentication.AuthenticationHandler),
    (r'/api/tokenauth', authentication.TokenAuthHandler),
    (r'/api/receiptauth', authentication.ReceiptAuthHandler),
    (r'/api/session', authentication.SessionHandler),
    (r'/api/tenantauthswitch/' + tid_regexp, authentication.TenantAuthSwitchHandler),

    # Public API
    (r'/api/public', public.PublicResource),

    # User Preferences Handler
    (r'/api/preferences', user.UserInstance),
    (r'/api/user/operations', user.operation.UserOperationHandler),

    # Token Handlers
    (r'/api/token', token.TokenHandler),

    # Submission Handlers
    (r'/api/submission', submission.SubmissionInstance),
    (r'/api/submission/attachment', attachment.SubmissionAttachment),

    # Receiver Handlers
    (r'/api/recipient/operations', receiver.Operations),
    (r'/api/rtips', receiver.TipsCollection),
    (r'/api/rtips/' + uuid_regexp, rtip.RTipInstance),
    (r'/api/rtips/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),
    (r'/api/rtips/' + uuid_regexp + r'/iars', rtip.IdentityAccessRequestsCollection),
    (r'/api/rtips/' + uuid_regexp + r'/export', export.ExportHandler),
    (r'/api/rtips/' + uuid_regexp + r'/wbfile', rtip.WhistleblowerFileHandler),
    (r'/api/rfile/' + uuid_regexp, rtip.ReceiverFileDownload),
    (r'/api/wbfile/' + uuid_regexp, rtip.RTipWBFileHandler),

    # Whistleblower Tip Handlers
    (r'/api/wbtip', wbtip.WBTipInstance),
    (r'/api/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/api/wbtip/rfile', attachment.PostSubmissionAttachment),
    (r'/api/wbtip/wbfile/' + uuid_regexp, wbtip.WBTipWBFileHandler),
    (r'/api/wbtip/' + uuid_regexp + r'/provideidentityinformation', wbtip.WBTipIdentityHandler),
    (r'/api/wbtip/' + uuid_regexp + r'/update', wbtip.WBTipAdditionalQuestionnaire),

    (r'/api/custodian/iars', custodian.IdentityAccessRequestsCollection),
    (r'/api/custodian/iars/' + uuid_regexp, custodian.IdentityAccessRequestInstance),

    # Email Validation Handler
    (r'/api/email/validation/(.+)', email_validation.EmailValidation),

    # Reset Password Handler
    (r'/api/reset/password', password_reset.PasswordResetHandler),
    (r'/api/reset/password/(.+)', password_reset.PasswordResetHandler),

    # Admin Handlers
    (r'/api/admin/node', admin_node.NodeInstance),
    (r'/api/admin/network', admin_network.NetworkInstance),
    (r'/api/admin/users', admin_user.UsersCollection),
    (r'/api/admin/users/' + uuid_regexp, admin_user.UserInstance),
    (r'/api/admin/contexts', admin_context.ContextsCollection),
    (r'/api/admin/contexts/' + uuid_regexp, admin_context.ContextInstance),
    (r'/api/admin/questionnaires', admin_questionnaire.QuestionnairesCollection),
    (r'/api/admin/questionnaires/duplicate', admin_questionnaire.QuestionnareDuplication),
    (r'/api/admin/questionnaires/' + key_regexp, admin_questionnaire.QuestionnaireInstance),
    (r'/api/admin/notification', admin_notification.NotificationInstance),
    (r'/api/admin/fields', admin_field.FieldsCollection),
    (r'/api/admin/fields/' + key_regexp, admin_field.FieldInstance),
    (r'/api/admin/steps', admin_step.StepCollection),
    (r'/api/admin/steps/' + uuid_regexp, admin_step.StepInstance),
    (r'/api/admin/fieldtemplates', admin_field.FieldTemplatesCollection),
    (r'/api/admin/fieldtemplates/' + key_regexp, admin_field.FieldTemplateInstance),
    (r'/api/admin/redirects', admin_redirect.RedirectCollection),
    (r'/api/admin/redirects/' + uuid_regexp, admin_redirect.RedirectInstance),
    (r'/api/admin/auditlog', admin_auditlog.AuditLog),
    (r'/api/admin/auditlog/access', admin_auditlog.AccessLog),
    (r'/api/admin/auditlog/debug', admin_auditlog.DebugLog),
    (r'/api/admin/auditlog/jobs', admin_auditlog.JobsTiming),
    (r'/api/admin/auditlog/tips', admin_auditlog.TipsCollection),
    (r'/api/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', admin_l10n.AdminL10NHandler),
    (r'/api/admin/config', admin_operation.AdminOperationHandler),
    (r'/api/admin/config/tls', https.ConfigHandler),
    (r'/api/admin/config/tls/files/(csr)', https.CSRFileHandler),
    (r'/api/admin/config/tls/files/(cert|chain|key)', https.FileHandler),
    (r'/api/admin/files', admin_file.FileCollection),
    (r'/api/admin/files/(.+)', admin_file.FileInstance),
    (r'/api/admin/tenants', admin_tenant.TenantCollection),
    (r'/api/admin/tenants/' + '([0-9]{1,20})', admin_tenant.TenantInstance),
    (r'/api/admin/submission_statuses', admin_submission_statuses.SubmissionStatusCollection),
    (r'/api/admin/submission_statuses/' + r'(closed)' + r'/substatuses', admin_submission_statuses.SubmissionSubStatusCollection),
    (r'/api/admin/submission_statuses/' + uuid_regexp, admin_submission_statuses.SubmissionStatusInstance),
    (r'/api/admin/submission_statuses/' + uuid_regexp + r'/substatuses', admin_submission_statuses.SubmissionSubStatusCollection),
    (r'/api/admin/submission_statuses/' + r'(closed)' + r'/substatuses/' + uuid_regexp, admin_submission_statuses.SubmissionSubStatusInstance),
    (r'/api/admin/submission_statuses/' + uuid_regexp + r'/substatuses/' + uuid_regexp, admin_submission_statuses.SubmissionSubStatusInstance),

    (r'/api/wizard', wizard.Wizard),
    (r'/api/signup', signup.Signup),
    (r'/api/signup/([a-zA-Z0-9_\-]{64})', signup.SignupActivation),

    (r'/api/support', support.SupportHandler),

    (r'/api/admin/config/acme/run', https.AcmeHandler),

    (r'/.well-known/acme-challenge/([a-zA-Z0-9_\-]{42,44})', https.AcmeChallengeHandler),
    (r'/.well-known/security.txt', security.SecuritytxtHandler),

    # Special Files Handlers
    (r'/robots.txt', robots.RobotstxtHandler),
    (r'/sitemap.xml', sitemap.SitemapHandler),
    (r'/s/(.+)', file.FileHandler),
    (r'/script', script.ScriptHandler),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', l10n.L10NHandler),

    (r'^(/admin|/login|/submission)$', redirect.SpecialRedirectHandler),

    (r'/(viewer/[a-zA-Z0-9_\-\/\.\@]*)', viewer.ViewerHandler),

    # This handler attempts to route all non routed get requests
    (r'/([a-zA-Z0-9_\-\/\.\@]*)', staticfile.StaticFileHandler)
]


class APIResourceWrapper(Resource):
    _registry = None
    isLeaf = True
    method_map = {
      'delete': 200,
      'head': 200,
      'get': 200,
      'options': 200,
      'post': 201,
      'put': 202
    }

    def __init__(self):
        Resource.__init__(self)
        self._registry = []
        self.handler = None

        for tup in api_spec:
            args = {}
            if len(tup) == 2:
                pattern, handler = tup
            else:
                pattern, handler, args = tup

            if not pattern.startswith("^"):
                pattern = "^" + pattern

            if not pattern.endswith("$"):
                pattern += "$"

            if not hasattr(handler, '_decorated'):
                handler._decorated = True
                for m in ['delete', 'get', 'put', 'post']:
                    # head and options method is intentionally not considered here
                    if hasattr(handler, m):
                        decorators.decorate_method(handler, m)

            self._registry.append((re.compile(pattern), handler, args))

    def should_redirect_https(self, request):
        if (State.tenants[1].cache.https_enabled or
            State.tenants[request.tid].cache.https_enabled) and \
           not request.isSecure() and \
           request.client_ip not in State.settings.local_hosts and \
           b'acme-challenge' not in request.path:
            return True

        return False

    def should_redirect_tor(self, request):
        if request.client_using_tor and \
           State.tenants[request.tid].cache.onionnames and \
           request.hostname != State.tenants[request.tid].cache.onionnames[0]:
            return True

        return False

    def redirect_https(self, request):
        request.redirect(b'https://' + State.tenants[request.tid].cache.hostname.encode() + request.path)

    def redirect_tor(self, request):
        request.redirect(b'http://' + State.tenants[request.tid].cache.onionnames[0] + request.path)

    def handle_exception(self, exception, request):
        """
        handle_exception is a callback that decorators all deferreds in render

        It responds to properly handled GL Exceptions by pushing the error msgs
        to the client and it spools a mail in the case the exception is unknown
        and unhandled.

        :param exception: A `Twisted.python.Failure` instance that wraps a `GLException`
                  or a normal `Exception`
        :param request: A `twisted.web.Request`
        """
        if request.finished:
            return

        e = exception

        if inspect.isclass(e):
            e = e()

        if isinstance(e, Failure):
            e = e.value

        if isinstance(e, NoResultFound):
            e = errors.ResourceNotFound
        elif isinstance(e, errors.GLException):
            pass
        else:
            e.tid = request.tid
            e.url = request.hostname + request.path
            extract_exception_traceback_and_schedule_email(exception)
            e = errors.InternalServerError('Unexpected')

        if isinstance(e, errors.GLException):
          request.setResponseCode(e.status_code)
          request.setHeader(b'content-type', b'application/json')

          response = json.dumps({
              'error_message': e.reason,
              'error_code': e.error_code,
              'arguments': getattr(e, 'arguments', [])
          })

          request.write(response.encode())

    def preprocess(self, request):
        request.hostname = request.getRequestHostname()
        request.port = request.getHost().port
        request.headers = request.getAllHeaders()
        request.client_ip = b''
        request.client_ua = b''
        request.client_using_mobile = False
        request.client_using_tor = False
        request.language = 'en'
        request.multilang = False
        request.finished = False

        if (not State.tenants[1].cache.wizard_done or
            request.hostname == b'localhost' or
            isIPAddress(request.hostname) or
            isIPv6Address(request.hostname)):
            request.tid = 1
        else:
            request.tid = State.tenant_hostname_id_map.get(request.hostname, None)

        if request.tid == 1:
            try:
                match1 = re.match(b'^/t/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})(/.*)', request.path)
                match2 = re.match(b'^/t/([0-9a-z\-]+)(/.*)$', request.path)

                if match1 is not None:
                    groups = match1.groups()
                    tid = State.tenant_uuid_id_map[groups[0].decode()]
                    request.tid, request.path = tid, groups[1]
                elif match2 is not None:
                    groups = match2.groups()
                    tid = State.tenant_subdomain_id_map[groups[0].decode()]
                    request.tid, request.path = tid, groups[1]
            except:
                pass

        if request.tid is None:
            # Tentative domain correction in relation to presence / absence of 'www.' prefix
            if not request.hostname.startswith(b'www.'):
                tentative_hostname = b'www.' + request.hostname
            else:
                tentative_hostname = request.hostname[4:]

            if tentative_hostname in State.tenant_hostname_id_map:
                request.tid = State.tenant_hostname_id_map[tentative_hostname]
                if State.tenants[request.tid].cache.https_enabled:
                    request.redirect(b'https://' + tentative_hostname + b'/')
                else:
                    request.redirect(b'http://' + tentative_hostname + b'/')
            else:
                # Fallback on root tenant with error 400
                request.tid = None
                return

        if request.tid is None or request.tid not in State.tenants:
            request.tid = None
            return

        request.client_ip = request.getClientIP()
        if isinstance(request.client_ip, bytes):
            request.client_ip = request.client_ip.decode()

        # Handle IPv4 mapping on IPv6
        if request.client_ip.startswith('::ffff:'):
            request.client_ip = request.client_ip[7:]

        request.client_using_tor = request.client_ip in State.tor_exit_set or \
                                   request.port == 8083

        request.client_ua = request.headers.get(b'user-agent', b'')

        request.client_using_mobile = re.search(b'Mobi|Android', request.client_ua, re.IGNORECASE) is not None

        request.language = self.detect_language(request)
        if b'multilang' in request.args:
            request.multilang = True

    def render(self, request):
        """
        :param request: `twisted.web.Request`

        :return: empty `str` or `NOT_DONE_YET`
        """
        self.preprocess(request)

        if request.tid is None:
            request.setResponseCode(400)
            return b''

        self.set_headers(request)

        if self.should_redirect_tor(request):
            self.redirect_tor(request)
            return b''

        if self.should_redirect_https(request):
            self.redirect_https(request)
            return b''

        request_path = request.path.decode()

        if request_path in State.tenants[request.tid].cache['redirects']:
            request.redirect(State.tenants[request.tid].cache['redirects'][request_path])
            return b''

        match = None
        for regexp, handler, args in self._registry:
            try:
                match = regexp.match(request_path)
            except UnicodeDecodeError:
                match = None
            if match:
                break

        if match is None:
            self.handle_exception(errors.ResourceNotFound, request)
            return b''

        method = request.method.lower().decode()

        if method == 'head':
            method = 'get'
        elif method == 'options':
            request.setResponseCode(200)
            return b''

        if method not in self.method_map.keys() or not hasattr(handler, method):
            self.handle_exception(errors.MethodNotImplemented, request)
            return b''

        f = getattr(handler, method)
        groups = match.groups()

        self.handler = handler(State, request, **args)

        request.setResponseCode(self.method_map[method])

        if self.handler.root_tenant_only and \
                request.tid != 1:
            self.handle_exception(errors.ForbiddenOperation, request)
            return b''

        if self.handler.root_tenant_or_management_only and \
                request.tid != 1 and \
                not self.handler.session.properties.get('management_session', False):
            self.handle_exception(errors.ForbiddenOperation, request)
            return b''

        if self.handler.upload_handler and method == 'post':
            self.handler.process_file_upload()
            if self.handler.uploaded_file is None:
                return b''

        @defer.inlineCallbacks
        def concludeHandlerFailure(err):
            yield self.handler.check_execution_time()
            self.handle_exception(err, request)

            if request.finished:
                return

            request.finish()

        @defer.inlineCallbacks
        def concludeHandlerSuccess(ret):
            """
            Concludes successful execution of a `BaseHandler` instance

            :param ret: A `dict`, `list`, `str`, `None` or something unexpected
            """
            yield self.handler.check_execution_time()

            if request.finished:
                return

            if ret is not None:
                if isinstance(ret, (dict, list)):
                    ret = json.dumps(ret, cls=JSONEncoder, separators=(',', ':'))
                    request.setHeader(b'content-type', b'application/json')

                if isinstance(ret, str):
                    ret = ret.encode()

                request.write(ret)

            request.finish()

        d = defer.maybeDeferred(f, self.handler, *groups).addCallbacks(concludeHandlerSuccess, concludeHandlerFailure)

        def _finish(_ret):
            request.finished = True

        request.notifyFinish().addBoth(_finish)
        request.notifyFinish().addErrback(lambda _: d.cancel())

        return NOT_DONE_YET

    def set_headers(self, request):
        request.setHeader(b'Server', b'GlobaLeaks')

        if request.isSecure():
            request.setHeader(b'Strict-Transport-Security',
                              b'max-age=31536000; includeSubDomains; preload')

            if State.tenants[request.tid].cache.onionservice:
                request.setHeader(b'Onion-Location', b'http://' + State.tenants[request.tid].cache.onionservice.encode() + request.path)

        if not State.settings.disable_csp:
            request.setHeader(b'Content-Security-Policy',
                              b"base-uri 'none';"
                              b"default-src 'none';"
                              b"form-action 'none';"
                              b"frame-ancestors 'none';"
                              b"sandbox;")

            request.setHeader(b"Cross-Origin-Embedder-Policy", "require-corp")
            request.setHeader(b"Cross-Origin-Opener-Policy", "same-origin")
            request.setHeader(b"Cross-Origin-Resource-Policy", "same-origin")

            # Disable features that could be used to deanonymize the user
            request.setHeader(b'Permissions-Policy', b"camera=(),"
                                                     b"document-domain=(),"
                                                     b"fullscreen=(),"
                                                     b"geolocation=(),"
                                                     b"microphone=()")

            # Prevent old browsers not supporting CSP frame-ancestors directive to includes the platform within an iframe
            request.setHeader(b'X-Frame-Options', b'deny')

        # Prevent the browsers to implement automatic mime type detection and execution.
        request.setHeader(b'X-Content-Type-Options', b'nosniff')

        # Disable caching
        # As by RFC 7234 Cache-control: no-store is the main directive instructing to not
        # store any entry to be used for caching; this settings make it not necessary to
        # use any other headers like Pragma and Expires.
        # This is described in section "3. Storing Responses in Caches"
        request.setHeader(b'Cache-control', b'no-store')

        # Avoid information leakage via referrer
        # This header instruct the browser to never inject the Referrer header in any
        # of the requests performed by xhr and via click on user links
        request.setHeader(b'Referrer-Policy', b'no-referrer')

        # to avoid Robots spidering, indexing, caching
        if State.tenants[request.tid].cache.allow_indexing:
            request.setHeader(b'X-Robots-Tag', b'noarchive')
        else:
            request.setHeader(b'X-Robots-Tag', b'noindex')

        if request.client_using_tor is True:
            request.setHeader(b'X-Check-Tor', b'True')
        else:
            request.setHeader(b'X-Check-Tor', b'False')

        request.setHeader(b'Content-Language', request.language)

    def detect_language(self, request):
        locales = []
        for language in request.headers.get(b'accept-language', b'').decode().split(","):
            parts = language.strip().split(";")
            if len(parts) > 1 and parts[1].startswith("q="):
                try:
                    score = float(parts[1][2:])
                except (ValueError, TypeError):
                    score = 0
            else:
                score = 1.0

            if parts[0] in State.tenants[request.tid].cache.languages_enabled:
                locales.append((parts[0], score))

        if locales:
            locales.sort(key=lambda pair: pair[1], reverse=True)
            return locales[0][0]

        return State.tenants[request.tid].cache.default_language
