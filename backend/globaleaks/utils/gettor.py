# -*- coding: utf-8 -*-

import os
import re

import json
import shutil

from distutils.version import LooseVersion

from twisted.internet import defer

from globaleaks.utils.agent import getPageSecurely, downloadPageSecurely

TB_DESC = 'https://www.torproject.org/projects/torbrowser/RecommendedTBBVersions'
TB_REPO = 'https://dist.torproject.org/torbrowser/'

TB_LOCALES=['ar', 'de', 'en', 'en-US', 'es-ES', 'fa', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt-PT', 'ru', 'tr', 'vi', 'zh-CN']

TB_REDIRECT_URLS = {
    'iphone': 'https://itunes.apple.com/us/app/onion-browser/id519296448',
    'android': 'https://play.google.com/store/apps/details?id=org.torproject.android'
}

class GetTor(object):
    def __init__(self, datadir):
        self.datadir = datadir
        self.current_version = 0
        self.file_latest_tb_version = os.path.join(self.datadir, 'latest_torbrowser.txt')

    def getCurrentVersion(self):
        """Return the current available version of the Tor Browser"""
        if os.path.exists(self.file_latest_tb_version):
            with open (latest_tb_file, 'r') as version_file:
                return version_file.read().replace('\n', '')

        return '0'

    def getOS(self, user_agent_header):
        """Get OS of an user given the user agent header"""

        if re.search('Windows Phone', user_agent_header):
            return 'windows'

        elif re.search('Windows', user_agent_header):
            return 'windows'

        elif re.search('Macintosh', user_agent_header):
            return 'osx'

        elif re.search('iPhone', user_agent_header):
            return 'iphone'

        elif re.search('iPad', user_agent_header):
            return 'ipad'

        elif re.search('Android', user_agent_header):
            return 'android'

        return 'other'

    def getLC(self, accept_language_header):
        """Get LC of an user given the accept language header"""
        def parse_accept_language(accept_language_header):
            return [l.split(';')[0] for l in accept_language_header.replace(" ", "").split(',')]

        def language_only(lc):
            if '-' in lc:
                lc = lc.split('-')[0]

            return lc

        for lc in parse_accept_language(accept_language_header):
            # returns es-PT if es-PT is available (perfect match)
            for l in TB_LOCALES:
                if lc.lower() == l.lower():
                    return l

            lc = language_only(lc)

            # returns es if asking for es-PT with
            # es-PT not available but es available
            for l in TB_LOCALES:
                if lc.lower() == l.lower():
                    return l

            # returns es-ES if asking for es-PT with
            # es-PT and es not available but  es-ES available
            for l in TB_LOCALES:
                if lc.lower() == language_only(l).lower():
                    return l

        return 'en-US'

    def getTB(self, os, lang):
        """Return TB Descriptor including path and content type"""

        if os == 'windows':
            return ('application/x-msdownload', 'torbrowser-install-%s_%s.exe' % (self.current_version, lang))
        elif os == 'osx':
            return ('application/x-apple-diskimage', 'TorBrowser-%s-osx32_%s.dmg' % (self.current_version, lang))

        return (None, None)

    def getTBFilenames(self, url, urls_regexp):
        """
        Return filenames listed on TB repository that match specified regexp

        :param: url (string) the TB repository
        :param: urls_regexp (regexp) the url regexp pattern
        """
        def extractLinks(data, urls_regexp):
            matches = re.findall(urls_regexp, data)
            return set(tuple(x[0] for x in matches))

        d = getPageSecurely(url)
        d.addCallback(extractLinks, urls_regexp)
        return d

    def getLatestTBVersion(self, versions):
        """
        Return the latest TB stable version among the version availables

        :param: versions (list) an array containing version numbers
        :return: return latest TB stable version
        """
        stable_version = None

        version_numbers = []
        for v in versions:
            if '-' not in v:
                version_numbers.append(v)

        stable_version = version_numbers[0]
        for v in version_numbers:
            if LooseVersion(v) < LooseVersion(stable_version):
                stable_version = v

        return stable_version

    @defer.inlineCallbacks
    def getTorTask(self):
        """
        Script to fetch the latest Tor Browser versions.

        Fetch the latest versions of Tor Browser from dist.torproject.org
        """
        # find out the latest version
        response = yield getPageSecurely(TB_DESC)

        latest_version = self.getLatestTBVersion(json.loads(response))

        # find out the current version delivered by GetTor static URL
        if self.current_version != latest_version:
            mirror = str('%s%s/' % (TB_REPO, latest_version))

            filenames_regexp = ''

            for lang in LOCALES:
                if filenames_regexp != '':
                    filenames_regexp += '|'

                filenames_regexp += "(%s.exe)|(%s.dmg)" % (lang, lang)

            url_regexp = 'href=[\'"]?([^\'" >]+(%s))' % filenames_regexp
            files = yield self.getTBFilenames(mirror, url_regexp)

            temp_path = os.path.join(self.datadir, 'temp')
            latest_path = os.path.join(self.datadir, 'latest')

            shutil.rmtree(temp_path, True)
            os.mkdir(temp_path)
            for f in files:
                url = str('%s%s/%s' % (dist_tpo, latest_version, f))
                savefile = os.path.join(temp_path, f)
                yield downloadPageSecurely(url, savefile)

            shutil.rmtree(latest_path, True)
            shutil.move(temp_path, latest_path)
 
            # if everything is OK, update the current version delivered by
            # GetTor static URL
            with open(self.file_latest_tb_version, 'w') as version_file:
                version_file.write(latest_version)

            self.current_version = latest_version
