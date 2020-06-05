# -*- coding: utf-8
#
# Handler implementing pre/post submission tokens for implementing rate limiting on whistleblower operations
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests


class TokenCreate(BaseHandler):
    """
    This class implement the handler for requesting a token.
    """
    check_roles = 'none'

    def post(self):
        """
        This API create a Token, a temporary memory only object able to keep
        track of the submission. If the system is under stress, complete the
        submission will require some actions to be performed before the
        submission can be concluded (e.g. hashcash and captchas).
        """
        request = self.validate_message(self.request.content.read(), requests.TokenReqDesc)

        return self.state.tokens.new(self.request.tid).serialize()


class TokenInstance(BaseHandler):
    """
    This class implements the handler for updating a token (e.g.: solving a captcha)
    """
    check_roles = 'none'

    def put(self, token_id):
        request = self.validate_message(self.request.content.read(), requests.TokenAnswerDesc)

        token = self.state.tokens.get(token_id)
        if token is None or self.request.tid != token.tid:
            raise errors.InvalidAuthentication

        token.update(request['answer'])

        return token.serialize()
