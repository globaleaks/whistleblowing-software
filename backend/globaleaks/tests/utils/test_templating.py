# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers import admin, public, recipient, user
from globaleaks.jobs.delivery import Delivery
from globaleaks.orm import tw
from globaleaks.tests import helpers
from globaleaks.utils.templating import Templating, supported_template_types


class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_keywords_conversion(self):
        tip_id = ''

        yield self.perform_full_submission_actions()
        yield Delivery().run()

        data = {}
        data['type'] = 'tip'
        data['user'] = yield user.get_user(1, self.dummyReceiver_1['id'], 'en')
        data['context'] = yield admin.context.get_context(1, self.dummyContext['id'], 'en')
        data['notification'] = yield tw(admin.notification.db_get_notification, 1, 'en')
        data['node'] = yield tw(admin.node.db_admin_serialize_node, 1, 'en')
        data['submission_statuses'] = yield tw(public.db_get_submission_statuses, 1, 'en')

        for tip in self.dummyRTips:
            if tip['receiver_id'] == self.dummyReceiver_1['id']:
                tip_id = tip['id']
                break

        data['tip'], _ = yield recipient.rtip.get_rtip(1, self.dummyReceiver_1['id'], tip_id, 'en')

        data['comments'] = data['tip']['comments']

        for key in ['tip', 'comment', 'file']:
            if key == 'tip':
                data['type'] = 'tip'
            else:
                data['type'] = 'tip_update'

            template = ''.join(supported_template_types[data['type']].keyword_list)
            Templating().format_template(template, data)
