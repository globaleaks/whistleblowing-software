# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.handlers import wbtip, rtip

class TestWhistleblowerFileWorkFlow(helpers.TestHandlerWithPopulatedDB):
    _handler = None

    @inlineCallbacks
    def test_get(self):
        file_description = "Status report for the submission."

        yield self.perform_full_submission_actions()

        self._handler = rtip.WhistleblowerFileHandler
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.post(rtip_desc['id'])

        self._handler = rtip.WhistleblowerFileInstanceHandler
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            for wbfile_desc in rtip_desc['wbfiles']:
                body = {
                  'description' : file_description
                }

                handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))
                yield handler.put(wbfile_desc['id'])

        self._handler = wbtip.WhistleblowerFileInstanceHandler
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            wbfiles_desc = yield self.get_wbfiles(wbtip_desc['id'])
            for wbfile_desc in wbfiles_desc:
                handler = self.request(role='whistleblower', user_id = wbtip_desc['id'])
                yield handler.get(wbfile_desc['id'])

        self._handler = rtip.WhistleblowerFileInstanceHandler
        rtips_desc = yield self.get_rtips()
        deleted_wbfiles_ids = []
        for rtip_desc in rtips_desc:
            for wbfile_desc in rtip_desc['wbfiles']:
                if wbfile_desc['id'] in deleted_wbfiles_ids:
                    continue

                self.assertEqual(wbfile_desc['description'], file_description)

                handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
                yield handler.delete(wbfile_desc['id'])
                deleted_wbfiles_ids.append(wbfile_desc['id'])

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.assertEqual(len(rtip_desc['wbfiles']), 0)
