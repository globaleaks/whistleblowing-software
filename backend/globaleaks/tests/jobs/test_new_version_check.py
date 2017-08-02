from distutils.version import StrictVersion # pylint: disable=no-name-in-module,import-error

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSettings
from globaleaks.jobs.update_check_sched import NewVerCheckJob
from globaleaks.tests import helpers


class TestExitNodesRefresh(helpers.TestGL):
    @inlineCallbacks
    def test_refresh_works(self):
        old_ver = StrictVersion('2.7.9')
        GLSettings.memory_copy.anonymize_outgoing_connections = False
        GLSettings.state.latest_version = old_ver

        yield NewVerCheckJob()._operation()

        self.assertGreater(GLSettings.state.latest_version, old_ver)
