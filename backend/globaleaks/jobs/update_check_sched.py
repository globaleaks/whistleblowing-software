# -*- encoding: utf-8 -*-
from debian import deb822
from distutils.version import StrictVersion as V # pylint: disable=no-name-in-module,import-error

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.error import ConnectionRefusedError

from globaleaks.settings import GLSettings
from globaleaks.jobs.base import LoopingJob
from globaleaks.utils.utility import log
from globaleaks.utils.agent import get_page


DEB_PACKAGE_URL = 'https://deb.globaleaks.org/xenial/Packages'


class UpdateCheckJob(LoopingJob):
    name = "Update Check"
    interval = 60*60*24
    threaded = False

    def fetch_packages_file(self):
        agent = GLSettings.get_agent()
        return get_page(agent, DEB_PACKAGE_URL)

    @inlineCallbacks
    def operation(self):
        try:
            log.debug('Fetching latest GlobaLeaks version from repository')
            p = yield self.fetch_packages_file()
            versions = [p['Version'] for p in deb822.Deb822.iter_paragraphs(p)]
            versions.sort(key=V)
            GLSettings.appstate.latest_version = versions[-1]
            log.debug('The newest version in the repository is: %s', GLSettings.appstate.latest_version)
        except ConnectionRefusedError as e:
            log.err('New version check failed: %s', e)
