# -*- coding: utf-8 -*-
from globaleaks.jobs.update_check_sched import UpdateCheckJob
from globaleaks.state import State
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks, succeed

packages="Package: globaleaks\n" \
         "Version: 0.0.1\n" \
         "Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         "Package: globaleaks\n" \
         "Version: 1.0.0\n" \
         "Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         "Package: globaleaks\n" \
         "Version: 1.2.3\n" \
         "Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         "Package: globaleaks\n" \
         "Version: 2.0.666\n" \
         "Filename: xenial/globaleaks_2.0.9_all.deb\n\n" \
         "Package: globaleaks\n" \
         "Version: 2.0.1337\n" \
         "Filename: xenial/globaleaks_2.0.100_all.deb\n\n" \
         "Package: tor2web\n" \
         "Version: 31337\n" \
         "Filename: xenial/tor2web_31337_all.deb\n\n"


class TestUpdateCheckJob(helpers.TestGL):
    @inlineCallbacks
    def test_refresh_works(self):
        State.tenant_cache[1].anonymize_outgoing_connections = False
        State.latest_version = '0.0.1'

        def fetch_packages_file_mock(self):
            return succeed(packages)

        UpdateCheckJob.fetch_packages_file = fetch_packages_file_mock

        yield UpdateCheckJob().operation()

        self.assertEqual(State.latest_version, '2.0.1337')
