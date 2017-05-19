# -*- coding: UTF-8
#
# exception

import json

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import send_exception_email
from globaleaks.utils.utility import log


class ExceptionHandler(BaseHandler):
    """
    This handler is responsible of receiving exceptions by the client
    and delivering them to the configured exception mail.
    """
    check_roles = 'unauthenticated'

    def post(self):
        """
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.ExceptionDesc)

        if not GLSettings.disable_client_exception_notification:
            exception_email = "URL: %s\n\n" % request['errorUrl']
            exception_email += "User Agent: %s\n\n" % request['agent']
            exception_email += "Error Message: %s\n\n" % request['errorMessage']
            exception_email += "Stacktrace:\n"
            exception_email += json.dumps(request['stackTrace'], indent=2)
            send_exception_email(exception_email)
            log.debug("Received client exception and passed error to exception mail handler")
