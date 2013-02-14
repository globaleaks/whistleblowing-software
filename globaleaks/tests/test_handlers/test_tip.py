import time
import unittest
from cyclone.util import ObjectDict as OD

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.rest import errors

from globaleaks import settings
from globaleaks.handlers import tip

class TestTipInstance(helpers.TestHandler):
    _handler = tip.TipInstance

    def login(self, role='wb', user_id=None):
        if not user_id:
            user_id = self.dummySubmission['submission_gus']
        wb_session = OD(timestamp=time.time(),id='spam',
                role=role, user_id=user_id)
        settings.sessions[wb_session.id] = wb_session
        return wb_session.id
 
    @inlineCallbacks
    def test_get_whistleblower_tip(self):
        tip_id = self.dummySubmission['context_gus']
        
        handler = self.request()
        handler.request.headers['X-Session'] = self.login()

        yield handler.get(tip_id)
        self.assertEqual(self.dummySubmission['fields'],
                self.responses[0]['fields'])

    def test_put_whistleblower_tip_fails(self):
        tip_id = self.dummySubmission['context_gus']
        
        handler = self.request()
        handler.request.headers['X-Session'] = self.login()
        d = handler.put(tip_id)
        self.assertFailure(d, errors.ForbiddenOperation)
        return d
    
    @unittest.skip("because not working atm")
    @inlineCallbacks
    def test_delete_receiver_tip(self):
        tip_id = self.dummySubmission['context_gus']
        self.dummySubmission['context_gus'] = {'spam': u'ham'}

        handler = self.request()
        handler.request.headers['X-Session'] = self.login('receiver')

        yield handler.delete(tip_id)

    @unittest.skip("because not working atm")
    @inlineCallbacks
    def test_put_global_delete_receiver_tip(self):
        req = {
            'total_delete': True,
            'is_pertinent': False
        }
        tip_id = self.dummySubmission['context_gus']
        self.dummySubmission['context_gus'] = {'spam': u'ham'}

        handler = self.request(req)
        handler.request.headers['X-Session'] = self.login('receiver')

        yield handler.put(tip_id)


# class TestTipCommentCollection(helpers.TestHandler):
#     _handler = tip.TipCommentCollection
# 
#     def test_get(self):
#         handler = self.request({})
#         return handler.get()
# 
#     def test_put(self):
#         handler = self.request({})
#         return handler.get()
# 
# class TestTipReceiversCollection(helpers.TestHandler):
#     _handler = tip.TipReceiversCollection
# 
#     def test_get(self):
#         handler = self.request({})
#         return handler.get()
# 
#     def test_post(self):
#         pass
# 
# 
