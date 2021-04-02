""" Deprecated interface to `debian.deb822` """
import warnings

warnings.warn("please use 'debian.deb822' instead", DeprecationWarning,
              stacklevel=2)

# pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
from debian.deb822 import *
