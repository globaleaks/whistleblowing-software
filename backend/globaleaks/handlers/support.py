# -*- coding: utf-8 -*-
#
# Handlers dealing with user support requests
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests
from globaleaks.utils.log import log


class SupportHandler(BaseHandler):
    """
    This handler is responsible of receiving support requests and forward them to administrators
    """
    check_roles = 'any'

    def post(self):
        request = self.validate_request(self.request.content.read(),
                                        requests.SupportDesc)

        email = "From: %s\n\n" % request['mail_address']
        email += "Site: %s\n\n" % request['url']
        email += "Request:\n%s" % request['text']
        self.state.schedule_support_email(self.request.tid, email)
        log.debug("Received support request and forwarded to administrators")
