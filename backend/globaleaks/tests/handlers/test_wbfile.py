# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.handlers import wbtip, rtip
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

class TestWBFileWorkFlow(helpers.TestHandlerWithPopulatedDB):
    _handler = None

    @inlineCallbacks
    def test_get(self):
        yield self.perform_full_submission_actions()

        self._handler = rtip.WhistleblowerFileHandler
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            samplefile = {'filename': 'hi.txt', 'body': 'Hello, world!', 'content_type': 'application/bogan'}
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], attached_file=samplefile)
            yield handler.post(rtip_desc['id'])

        self._handler = wbtip.WBTipWBFileHandler
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            wbfiles_desc = yield self.get_wbfiles(wbtip_desc['id'])
            for wbfile_desc in wbfiles_desc:
                handler = self.request(role='whistleblower', user_id = wbtip_desc['id'])
                yield handler.get(wbfile_desc['id'])

        self._handler = rtip.RTipWBFileHandler
        rtips_desc = yield self.get_rtips()
        deleted_wbfiles_ids = []
        for rtip_desc in rtips_desc:
            for wbfile_desc in rtip_desc['wbfiles']:
                if wbfile_desc['id'] in deleted_wbfiles_ids:
                    continue

                self.assertEqual(wbfile_desc['description'], 'description')

                handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
                yield handler.delete(wbfile_desc['id'])

                deleted_wbfiles_ids.append(wbfile_desc['id'])

                yield self.test_model_count(models.SecureFileDelete, len(deleted_wbfiles_ids))

        # check that the files are effectively gone from the db
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.assertEqual(len(rtip_desc['wbfiles']), 0)
