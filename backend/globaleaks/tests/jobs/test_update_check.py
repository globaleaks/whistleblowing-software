# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks, succeed

from globaleaks import models
from globaleaks.jobs.update_check import UpdateCheck
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.tests import helpers

packages=b"Package: globaleaks\n" \
         b"Version: 0.0.1\n" \
         b"Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         b"Package: globaleaks\n" \
         b"Version: 1.0.0\n" \
         b"Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         b"Package: globaleaks\n" \
         b"Version: 1.2.3\n" \
         b"Filename: xenial/globaleaks_1.0.0_all.deb\n\n" \
         b"Package: globaleaks\n" \
         b"Version: 2.0.666\n" \
         b"Filename: xenial/globaleaks_2.0.9_all.deb\n\n" \
         b"Package: globaleaks\n" \
         b"Version: 2.0.1337\n" \
         b"Filename: xenial/globaleaks_2.0.100_all.deb\n\n" \
         b"Package: tor2web\n" \
         b"Version: 31337\n" \
         b"Filename: xenial/tor2web_31337_all.deb\n\n"


@transact
def set_latest_version(session, version):
    return ConfigFactory(session, 1, 'node').set_val(u'latest_version', version)


@transact
def get_latest_version(session):
    return ConfigFactory(session, 1, 'node').get_val(u'latest_version')


class TestUpdateCheck(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_refresh_works(self):
        State.tenant_cache[1].anonymize_outgoing_connections = False

        yield set_latest_version('0.0.1')
        yield self.test_model_count(models.Mail, 0)

        def fetch_packages_file_mock(self):
            return succeed(packages)

        UpdateCheck.fetch_packages_file = fetch_packages_file_mock

        yield UpdateCheck().operation()

        latest_version = yield get_latest_version()
        self.assertEqual(latest_version, '2.0.1337')
        yield self.test_model_count(models.Mail, 1)
