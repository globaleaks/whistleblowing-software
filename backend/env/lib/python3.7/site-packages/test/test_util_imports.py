from twisted.trial import unittest

import sys
import functools
from unittest import skipUnless
import six


def fake_import(orig, name, *args, **kw):
    if name in ['GeoIP']:
        raise ImportError('testing!')
    return orig(*((name,) + args), **kw)


class TestImports(unittest.TestCase):

    @skipUnless(six.PY2 and 'pypy' not in sys.version.lower(), "Doesn't work in PYPY, Py3")
    def test_no_GeoIP(self):
        """
        Make sure we don't explode if there's no GeoIP module
        """

        global __import__
        orig = __import__
        try:
            # attempt to ensure we've unimportted txtorcon.util
            try:
                del sys.modules['txtorcon.util']
            except KeyError:
                pass
            import gc
            gc.collect()

            # replace global import with our test import, which will
            # throw on GeoIP import no matter what
            global __builtins__
            __builtins__['__import__'] = functools.partial(fake_import, orig)

            # now ensure we set up all the databases as "None" when we
            # import w/o the GeoIP thing available.
            import txtorcon.util
            loc = txtorcon.util.NetLocation('127.0.0.1')
            self.assertEqual(loc.city, None)
            self.assertEqual(loc.asn, None)
            self.assertEqual(loc.countrycode, '')

        finally:
            __import__ = orig
