# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers import admin, rtip
from globaleaks.jobs.delivery import Delivery
from globaleaks.tests import helpers
from globaleaks.utils.templating import Templating, supported_template_types


class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_keywords_conversion(self):
        yield self.perform_full_submission_actions()
        yield Delivery().run()

        data = {}
        data['type'] = 'tip'
        data['user'] = yield admin.user.get_user(1, self.dummyReceiver_1['id'], u'en')
        data['context'] = yield admin.context.get_context(1, self.dummyContext['id'], u'en')
        data['notification'] = yield admin.notification.get_notification(1, u'en')
        data['node'] = yield admin.node.admin_serialize_node(1, u'en')

        for tip in self.dummyRTips:
            if tip['receiver_id'] == self.dummyReceiver_1['id']:
                tip_id = tip['id']
                break

        data['tip'] = yield rtip.get_rtip(1, self.dummyReceiver_1['id'], tip_id, u'en')

        data['comments'] = data['tip']['comments']
        data['comment'] = data['comments'][0]

        data['messages'] = data['tip']['messages']
        data['message'] = data['messages'][0]

        files = yield rtip.receiver_get_rfile_list(1, data['tip']['id'])
        data['file'] = files[0]

        for key in ['tip', 'comment', 'message', 'file']:
            data['type'] = key
            template = ''.join(supported_template_types[key].keyword_list)
            Templating().format_template(template, data)
