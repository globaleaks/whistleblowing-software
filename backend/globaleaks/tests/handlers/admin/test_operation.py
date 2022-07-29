# -*- coding: utf-8
from globaleaks import models
from globaleaks.handlers.admin.operation import AdminOperationHandler
from globaleaks.jobs import delivery
from globaleaks.rest import errors
from globaleaks.tests import helpers

from twisted.internet import defer


class TestAdminPasswordReset(helpers.TestHandlerWithPopulatedDB):
    _handler = AdminOperationHandler

    @defer.inlineCallbacks
    def test_put(self):
        data_request = {
            'operation': 'reset_user_password',
            'args': {
                'value': self.dummyReceiver_1['id']
            }
        }

        handler = self.request(data_request, role='admin')

        yield handler.put()


class TestAdminResetSubmissions(helpers.TestHandlerWithPopulatedDB):
    _handler = AdminOperationHandler

    @defer.inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield delivery.Delivery().run()

    @defer.inlineCallbacks
    def test_put(self):
        yield self.test_model_count(models.InternalTip, 2)
        yield self.test_model_count(models.ReceiverTip, 4)
        yield self.test_model_count(models.InternalFile, 4)
        yield self.test_model_count(models.ReceiverFile, 8)
        yield self.test_model_count(models.Comment, 6)
        yield self.test_model_count(models.Message, 8)
        yield self.test_model_count(models.Mail, 0)

        data_request = {
            'operation': 'reset_submissions',
            'args': {}
        }

        handler = self.request(data_request, role='admin')

        yield self.assertRaises(errors.InvalidAuthentication, handler.put)

        handler.require_confirmation = []

        yield handler.put()

        yield self.test_model_count(models.InternalTip, 0)
        yield self.test_model_count(models.ReceiverTip, 0)
        yield self.test_model_count(models.InternalFile, 0)
        yield self.test_model_count(models.ReceiverFile, 0)
        yield self.test_model_count(models.Comment, 0)
        yield self.test_model_count(models.Message, 0)
        yield self.test_model_count(models.Mail, 0)


class TestAdminOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = AdminOperationHandler

    def _test_operation_handler(self, operation):
        data_request = {
            'operation': operation,
            'args': {}
        }

        handler = self.request(data_request, role='admin')

        handler.require_confirmation = []

        return handler.put()

    def test_admin_test_mail(self):
        return self._test_operation_handler('test_mail')

    def test_admin_test_smtp_settings(self):
        return self._test_operation_handler('reset_smtp_settings')

    def test_admin_test_toggle_escrow(self):
        return self._test_operation_handler('toggle_escrow')

    def test_admin_test_reset_templates(self):
        return self._test_operation_handler('reset_templates')
