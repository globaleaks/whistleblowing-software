# -*- coding: UTF-8

# This mock is required in order to make python-acmne 0.4.1 compatible with:
# -
# - https://github.com/certbot/certbot/issues/4877

from acme import messages, util

def mock_Directory__init__(self, jobj):
    canon_jobj = util.map_keys(jobj, self._canon_key)
    self._jobj = canon_jobj

messages.Directory.__init__ = mock_Directory__init__

