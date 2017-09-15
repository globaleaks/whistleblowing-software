# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks, succeed

from globaleaks import models
from globaleaks.jobs.update_check_sched import UpdateCheckJob
from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.tests import helpers

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


@transact
def set_latest_version(store, version):
    return PrivateFactory(store, 1).set_val(u'latest_version', version)


@transact
def get_latest_version(store):
    return PrivateFactory(store, 1).get_val(u'latest_version')


class TestUpdateCheckJob(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_refresh_works(self):
        State.tenant_cache[1].anonymize_outgoing_connections = False

        yield set_latest_version('0.0.1')
        yield self.test_model_count(models.Mail, 0)

        def fetch_packages_file_mock(self):
            return succeed(packages)

        UpdateCheckJob.fetch_packages_file = fetch_packages_file_mock

        yield UpdateCheckJob().operation()

        latest_version = yield get_latest_version()
        self.assertEqual(latest_version, '2.0.1337')
        yield self.test_model_count(models.Mail, 1)
