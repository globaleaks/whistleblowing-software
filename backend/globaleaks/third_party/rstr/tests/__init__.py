import unittest
import test_rstr
import test_xeger
import test_package_level_access


def suite():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_rstr)
    suite.addTests(loader.loadTestsFromModule(test_xeger))
    suite.addTests(loader.loadTestsFromModule(test_package_level_access))
    return suite
