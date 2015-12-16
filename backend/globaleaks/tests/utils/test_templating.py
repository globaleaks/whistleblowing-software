# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import admin
from globaleaks.utils.templating import Templating


class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_keywords_conversion(self):
        yield self.perform_full_submission_actions()

        data = {}
        data['type'] = 'tip'
        data['receiver'] = yield admin.receiver.get_receiver(self.dummyReceiver_1['id'], 'en')
        data['context'] = yield admin.context.get_context(self.dummyContext['id'], 'en')
        data['notification'] = yield admin.notification.get_notification('en')
        data['node'] = yield admin.node.admin_serialize_node('en')
        data['tip'] = self.dummyRTips[0]

        subject, body = Templating().get_mail_subject_and_body(data)
 
        self.assertSubstring(data['node']['public_site'], body)
        self.assertSubstring(data['node']['hidden_service'], body)
