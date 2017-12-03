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
            1: ('www.globaleaks.org',
                'aaaaaaaaaaaaaaaa.onion',
                'p1.www.globaleaks.org',
                'p1.aaaaaaaaaaaaaaaa.onion'),
            2: ('www.domain-a.com',
                'p2.www.globaleaks.org',
                'tenant-2.www.globaleaks.org',
                'p2.aaaaaaaaaaaaaaaa.onion',
                'tenant-2.aaaaaaaaaaaaaaaa.onion',
                'bbbbbbbbbbbbbbbb.onion'),
            3: ('www.domain-b.com',
                'p3.www.globaleaks.org',
                'tenant-3.www.globaleaks.org',
                'p3.aaaaaaaaaaaaaaaa.onion',
                'tenant-3.aaaaaaaaaaaaaaaa.onion',
                'cccccccccccccccc.onion')
        }

        for tid, case_tup in cases.items():
            for hostname in case_tup:
                mapped_tid = State.tenant_hostname_id_map[hostname]
                self.assertEqual(mapped_tid, tid)
