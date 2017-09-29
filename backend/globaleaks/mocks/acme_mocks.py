# -*- coding: utf-8

# This mock is required in order to make python-acme 0.4.1 compatible with:
# - https://community.letsencrypt.org/t/adding-random-entries-to-the-directory/33417
# - https://github.com/certbot/certbot/issues/4877
from acme import messages, util

def mock_Directory__init__(self, jobj):
    canon_jobj = util.map_keys(jobj, self._canon_key)
    self._jobj = canon_jobj

messages.Directory.__init__ = mock_Directory__init__

# Backport patch https://github.com/certbot/certbot/pull/3990
import sys

if sys.version_info < (2, 7, 9):  # pragma: no cover
    import requests

    try:
        requests.packages.urllib3.contrib.pyopenssl.inject_into_urllib3()
    except AttributeError:
        import urllib3

        class Object:
            pass

        requests.packages = Object()
        requests.packages.urllib3 = urllib3
