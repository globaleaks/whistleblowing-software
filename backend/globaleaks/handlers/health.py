# -*- coding: utf-8 -*-
#
# Implementation of health status resource
from globaleaks.handlers.base import BaseHandler


class HealthStatusHandler(BaseHandler):
    """
    Handler that implements health status checks
    """
    check_roles = 'any'

    def get(self):
        """
        Get the health status
        """
        return "OK"
