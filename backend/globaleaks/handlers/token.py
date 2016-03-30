# -*- coding: UTF-8
#
# token
# **********
#
# Implements an API for gettin/updating tokens to be used for performing user operations
# subject in general to rate limit.

from globaleaks.handlers.base import BaseHandler
from globaleaks.utils.token import Token, TokenList
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings


class TokenCreate(BaseHandler):
    """
    This class implement the handler for requesting a token.
    """
    @BaseHandler.unauthenticated
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
        request = self.validate_message(self.request.body, requests.TokenReqDesc)

        if request['type'] == 'submission':
            if not GLSettings.accept_submissions:
                raise errors.SubmissionDisabled

            # TODO implement further validations for different token options based on type
            # params = self.validate_message(request['params'], requests.TokenParamsSubmissionDesc)

        token = Token(request['type'])

        self.set_status(201) # Created
        self.write(token.serialize())


class TokenInstance(BaseHandler):
    """
    This class impleement the handler for updating a token (e.g.: solving a captcha)
    """
    @BaseHandler.unauthenticated
    def put(self, token_id):
        """
        Parameter: token_id
        Request: TokenAnswerDesc
        Response: TokenDesc
        """
        request = self.validate_message(self.request.body, requests.TokenAnswerDesc)

        token = TokenList.get(token_id)
        token.update(request)

        self.set_status(202) # Updated
        self.write(token.serialize())
