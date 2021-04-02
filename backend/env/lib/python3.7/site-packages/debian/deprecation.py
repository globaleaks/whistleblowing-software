# -*- coding: utf-8 -*- vim: fileencoding=utf-8 :

""" Utility module to deprecate features """

# Copyright © Ben Finney <ben+debian@benfinney.id.au>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import warnings


def function_deprecated_by(func):
    """ Return a function that warns it is deprecated by another function.

        Returns a new function that warns it is deprecated by function
        ``func``, then acts as a pass-through wrapper for ``func``.

    """
    try:
        func_name = func.__name__
    except AttributeError:
        func_name = func.__func__.__name__
    warn_msg = "Use %s instead" % func_name
    def deprecated_func(*args, **kwargs):
        warnings.warn(warn_msg, DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return deprecated_func
