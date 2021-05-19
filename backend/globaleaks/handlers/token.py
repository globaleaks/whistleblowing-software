# -*- coding: utf-8
#
# Handler implementing pre/post submission tokens for implementing rate limiting on whistleblower operations
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.state import State


def generate_token(tid, session):
    return State.tokens.new(tid, session).serialize()



class TokenCreate(BaseHandler):
    """
    This class implement the handler for requesting a token.
    """
    check_roles = 'any'

    def post(self):
        """
        This API create a Token, a temporary memory only object able to
        keep track and limit user actions.
        """
        return generate_token(self.request.tid, self.session)


class TokenInstance(BaseHandler):
    """
    This class implements the handler for updating a token (e.g.: solving a captcha)
    """
    check_roles = 'any'

    def put(self, token_id):
        request = self.validate_message(self.request.content.read(), requests.TokenAnswerDesc)

        token = self.state.tokens.get(token_id)
        if token is None or self.request.tid != token.tid:
            raise errors.InvalidAuthentication

        token.update(request['answer'])

        return token.serialize()
