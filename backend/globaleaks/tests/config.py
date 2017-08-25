import argparse
import sys

from twisted.trial import unittest


def exec_parser():
    op = argparse.ArgumentParser()
    op.add_argument("--skip-migs", nargs=0, action=SkipMigrations, default=0, help="Skip running migrations")
    op.add_argument("--skip-modules", nargs=1, type=str, action=SkipModules, default=[], help="A list of modules to skip seperated by commas: tests.handlers,tests.test_security")
    op.parse_known_args()

modules_to_skip = list()

tests_to_ignore = {
  'migration': False,
}


class SkipMigrations(argparse.Action):
    def __call__(self, *args):
        tests_to_ignore['migration'] = True
        sys.argv.remove('--skip-migs')


class SkipModules(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        mods = values[0]
        global modules_to_skip
        modules_to_skip = mods.split(',')
        sys.argv = [x for x in sys.argv if
                      not x.startswith('--skip-modules') or not x.endswith(mods)]


def skipIf(case):
  if tests_to_ignore.get(case, False):
    raise unittest.SkipTest('TestCase ignored by flag: %s' % case)
  else:
      pass


def skipCase(testcase):
    for skipped_module in modules_to_skip:
        tc_mod_path = testcase.__module__.split('.')
        mod_target = skipped_module.split('.')[-1]
        if mod_target in tc_mod_path:
            raise unittest.SkipTest('TestCase excluded by: %s' % skipped_module)
