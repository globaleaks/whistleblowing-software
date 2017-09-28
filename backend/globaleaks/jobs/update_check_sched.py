# -*- encoding: utf-8 -*-
from distutils.version import LooseVersion as V  # pylint: disable=no-name-in-module,import-error

from debian import deb822
from globaleaks.jobs.base import ExternNetLoopingJob
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.agent import get_page
from globaleaks.utils.utility import log
from twisted.internet.defer import inlineCallbacks


DEB_PACKAGE_URL = 'https://deb.globaleaks.org/xenial/Packages'


class UpdateCheckJob(ExternNetLoopingJob):
    name = "Update Check"
    interval = 60*60*24
    threaded = False

    def fetch_packages_file(self):
        return get_page(Settings.get_agent(), DEB_PACKAGE_URL)

    @inlineCallbacks
    def operation(self):
        log.debug('Fetching latest GlobaLeaks version from repository')
        packages_file = yield self.fetch_packages_file()
        versions = [p['Version'] for p in deb822.Deb822.iter_paragraphs(packages_file) if p['Package'] == 'globaleaks']
        versions.sort(key=V)
        State.latest_version = versions[-1]
        log.debug('The newest version in the repository is: %s', State.latest_version)
