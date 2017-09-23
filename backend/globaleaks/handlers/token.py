# -*- coding: UTF-8
#
# token
# **********
#
# Implements an API for gettin/updating tokens to be used for performing user operations
# subject in general to rate limit.

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.token import Token, TokenList


class TokenCreate(BaseHandler):
    """
    This class implement the handler for requesting a token.
    """
    check_roles = 'unauthenticated'

    def post(self):
        """
        Request: None
        Response: TokenDesc (Token)
        Errors: InvalidInputFormat

        This API create a Token, a temporary memory only object able to keep
        track of the submission. If the system is under stress, complete the
        submission will require some actions to be performed before the
        submission can be concluded (e.g. hashcash and captchas).
        """
        if not self.request.client_using_tor and not GLSettings.memory_copy.accept_tor2web_access['whistleblower']:
            raise errors.TorNetworkRequired

        request = self.validate_message(self.request.content.read(), requests.TokenReqDesc)

        if request['type'] == 'submission' and not GLSettings.accept_submissions:
            raise errors.SubmissionDisabled

        token = Token(request['type'])

        if not self.request.client_using_tor and self.request.client_proto == 'http':
            # Due to https://github.com/globaleaks/GlobaLeaks/issues/2088 the proof of work if currently
            # implemented only over Tor and HTTPS that are the production conditions.
            token.proof_of_work['solved'] = True

        return token.serialize()


class TokenInstance(BaseHandler):
    """
    This class impleement the handler for updating a token (e.g.: solving a captcha)
    """
    check_roles = 'unauthenticated'

    def put(self, token_id):
        """
        Parameter: token_id
        Request: TokenAnswerDesc
        Response: TokenDesc
        """
        request = self.validate_message(self.request.content.read(), requests.TokenAnswerDesc)

        token = TokenList.get(token_id)

        if not token.update(request):
            raise errors.TokenFailure('failed challenge')

        return token.serialize()
