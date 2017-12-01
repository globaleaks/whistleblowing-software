from twisted.internet.defer import inlineCallbacks

from globaleaks import db
from globaleaks.state import State

from globaleaks.tests import helpers


class TestMemCache(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_refresh_tenant_cache(self):
        yield db.refresh_memory_variables()

        self.assertEqual(len(State.tenant_cache), 3)

        cases = {
            1: ('root.system', 'p1.root.system', 'xxx.root.system',
                'p1.aaaaaaaaaaaaaaaa.onion', 'aaaaaaaaaaaaaaaa.onion',
                'sub.aaaaaaaaaaaaaaaa.onion'),
            2: ('b.domain.com', 'p2.root.system', 'sub.root.system',
                'p1.bbbbbbbbbbbbbbbb.onion', 'bbbbbbbbbbbbbbbb.onion',
                'sub.bbbbbbbbbbbbbbbb.onion'),
            3: ('c.domain.com', 'p3.root.system', 'sub.root.system',
                'p1.cccccccccccccccc.onion', 'cccccccccccccccc.onion',
                'sub.cccccccccccccccc.onion'),
        }
        # TODO ensure subdomains do not collide

        print('State.tostname_id_map\n %s' % State.tenant_hostname_id_map)
        for tid, case_tup in cases.items():
            for hostname in case_tup:
                mapped_tid = State.tenant_hostname_id_map[hostname]
                self.assertEqual(mapped_tid, tid)
