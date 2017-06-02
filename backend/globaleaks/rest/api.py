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

from globaleaks.rest import apicache, requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import randbits


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
    (r'/admin/config/tls/files/(csr)', https.CSRFileHandler),
    (r'/admin/config/tls/files/(cert|chain|priv_key)', https.FileHandler),
    (r'/admin/staticfiles$', admin_staticfiles.StaticFileList),
    (r'/admin/staticfiles/(.+)', admin_staticfiles.StaticFileInstance),
    (r'/admin/overview/tips', admin_overview.Tips),
    (r'/admin/overview/files', admin_overview.Files),
    (r'/wizard', wizard.Wizard),

    ## Special Files Handlers##
    (r'/robots.txt', robots.RobotstxtHandler),
    (r'/sitemap.xml', robots.SitemapHandler),
    (r'/s/(.+)', base.StaticFileHandler, {'path': GLSettings.static_path}),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', l10n.L10NHandler),

    ## This Handler should remain the last one as it works like a last resort catch 'em all
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
            args = None
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
        handle = False
        if isinstance(e, errors.GLException):
            handle = True
        elif isinstance(e.value, errors.GLException):
            e = e.value
            handle = True

        if handle:
            request.setResponseCode(e.status_code)

            request.write({
                'error_message': e.reason,
                'error_code': e.error_code,
                'arguments': getattr(e, 'arguments', [])
            })

    def render(self, request):
        request_finished = [False]

        def _finish(_):
            request_finished[0] = True

        request.notifyFinish().addBoth(_finish)

        method = request.method.lower()

        if method not in ['get', 'post', 'put', 'delete']:
            self.handle_exception(errors.MethodNotImplemented(), request)
            return NOT_DONE_YET

        for regexp, handler, args in self._registry:
            match = regexp.match(request.path)
            if not match:
                continue

            if args is None:
                args = {}

            groups = [unicode(g) for g in match.groups()]

            h = handler(request, **args)

            f = getattr(h, method, None)

            if f is None:
                self.handle_exception(errors.MethodNotImplemented(), request)
                return ''

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
        request.setReponseCode(202)
        return self.render(self, request)

    def render_POST(self, request):
        request.setReponseCode(201)
        return self.render(self, request)
