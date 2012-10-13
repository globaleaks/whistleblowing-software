# -*- encoding: utf-8 -*-
#
# This script is to be used to automagically generate the recurring data types
# documentation based on the API specification.
#
# to run it just do:
#
#   $ python generate_spec.py > outputfile.md
#
# :authors: Arturo Filastò
# :licence: see LICENSE


import inspect
from globaleaks.messages import base
from utils import cleanup_docstring

def create_spec(spec):
    doc = ""
    for k, v in spec.items():
        doc += "    %s: %s\n" % (k, v)
    return doc

def create_class_doc(klass):
    doc = "## %s\n" % klass.__name__
    if klass.__doc__:
        cleanup_docstring(klass.__doc__)
    doc += "\n"
    doc += create_spec(klass.specification)
    doc += "\n\n"
    return doc

def create_special_doc(klass):
    doc = "  * %s: '%s'\n\n" % (klass.__name__, klass.regexp)
    return doc

types_doc = ""
special_doc = ""
for name, klass in inspect.getmembers(base, inspect.isclass):
    if issubclass(klass, base.GLTypes) and klass != base.GLTypes:
        types_doc += create_class_doc(klass)
    elif issubclass(klass, base.SpecialType) and klass != base.SpecialType:
        special_doc += create_special_doc(klass)

print "# Simple data elements\n"
print special_doc
print "# Complex data elements"
print types_doc
