# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks
from twisted.scripts._twistd_unix import ServerOptions

from globaleaks.runner import GlobaLeaksRunner
from globaleaks.tests import helpers


class TestRunner(helpers.TestGL):
    @inlineCallbacks
    def test_runner(self):
        # TODO: currently this test is mainly fake and is intended at list to
        #       spot errors like typos etcetera by raising the code coverage

        config = ServerOptions()

        globaleaks_runner = GlobaLeaksRunner(config)

        yield globaleaks_runner.start_globaleaks()
