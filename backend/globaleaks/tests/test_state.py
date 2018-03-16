# -*- coding: utf-8 -*-
import sys
from twisted.internet.defer import inlineCallbacks
from twisted.python.failure import Failure

from globaleaks import models
from globaleaks.state import mail_exception_handler, extract_exception_traceback_and_schedule_email
from globaleaks.tests import helpers


class TestMailUtils(helpers.TestGL):
    #from globaleaks.backend import mail_exception_handler, extract_exception_traceback_and_schedule_email

    @inlineCallbacks
    def test_mail_exception_handler(self):
        yield self.test_model_count(models.Mail, 0)
        mail_exception_handler(*sys.exc_info())
        yield self.test_model_count(models.Mail, 1)

    @inlineCallbacks
    def test_extract_exception_traceback_and_schedule_email(self):
        yield self.test_model_count(models.Mail, 0)
        extract_exception_traceback_and_schedule_email(Exception())
        yield self.test_model_count(models.Mail, 1)
        extract_exception_traceback_and_schedule_email(Failure(Exception()))
        yield self.test_model_count(models.Mail, 2)
