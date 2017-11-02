# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers import admin, rtip
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.tests import helpers
from globaleaks.utils.templating import Templating, supported_template_types

XTIDX = 1


class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_keywords_conversion(self):
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().run()

        data = {}
        data['type'] = 'tip'
        data['user'] = yield admin.user.get_user(XTIDX, self.dummyReceiver_1['id'], u'en')
        data['context'] = yield admin.context.get_context(XTIDX, self.dummyContext['id'], u'en')
        data['notification'] = yield admin.notification.get_notification(u'en')
        data['node'] = yield admin.node.admin_serialize_node(XTIDX, u'en')

        if self.dummyRTips[0]['receiver_id'] == self.dummyReceiver_1['id']:
            tip_id = self.dummyRTips[0]['id']
        else:
            tip_id = self.dummyRTips[1]['id']

        data['tip'] = yield rtip.get_rtip(self.dummyReceiver_1['id'], tip_id, u'en')

        data['comments'] = data['tip']['comments']
        data['comment'] = data['comments'][0]

        data['messages'] = data['tip']['messages']
        data['message'] = data['messages'][0]

        files = yield rtip.receiver_get_rfile_list(data['tip']['id'])
        data['file'] = files[0]

        for key in ['tip', 'comment', 'message', 'file']:
            data['type'] = key
            template = ''.join(supported_template_types[key].keyword_list)
            Templating().format_template(template, data)
