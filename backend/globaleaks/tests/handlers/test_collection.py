# -*- coding: utf-8 -*-
import shutil

from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact_ro
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.handlers import collection
from globaleaks.models import ReceiverTip
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers

class TestCollectionDownload(helpers.TestHandlerWithPopulatedDB):
    _handler = collection.CollectionDownload

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().operation()

    @inlineCallbacks
    def test_download(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request({}, role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']
            yield handler.post(rtip_desc['id'])
