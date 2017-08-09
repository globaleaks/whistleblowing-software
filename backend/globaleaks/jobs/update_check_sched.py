# -*- encoding: utf-8 -*-
from debian import deb822
from distutils.version import StrictVersion as v # pylint: disable=no-name-in-module,import-error

from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import ConnectionRefusedError

from globaleaks.settings import GLSettings
from globaleaks.jobs.base import LoopingJob
from globaleaks.utils.utility import log
from globaleaks.utils.agent import get_page


DEB_PACKAGE_URL = 'https://deb.globaleaks.org/xenial/Packages'


class NewVerCheckJob(LoopingJob):
    name = "Update Check"
    interval = 60*60*24
    threaded = False

    @inlineCallbacks
    def operation(self):
        net_agent = GLSettings.get_agent()
        try:
            log.debug('Fetching latest version from repo')
            r = yield get_page(net_agent, DEB_PACKAGE_URL)
            packages = [p for p in deb822.Deb822.iter_paragraphs(r)]
            new = sorted(packages, key=lambda x: v(x['Version']), reverse=True)

            GLSettings.appstate.latest_version = v(new[0]['Version'])
            log.debug('The newest version in the repo: %s' % GLSettings.appstate.latest_version)
        except ConnectionRefusedError as e:
            log.err('New version check failed: %s' % e)
