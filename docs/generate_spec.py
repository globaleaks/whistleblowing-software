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
from globaleaks.rest.messages import base

def create_spec(spec):
    doc = ""
    for k, v in spec.items():
        doc += "    %s: %s\n" % (k, v)
    return doc

def create_class_doc(klass):
    doc = "## %s\n" % klass.__name__
    if klass.__doc__:
        docstring = [line.strip() for line in klass.__doc__.split("\n")]
        doc += '\n'.join(docstring)
    doc += "\n"
    doc += create_spec(klass.specification)
    return doc

for name, klass in inspect.getmembers(base, inspect.isclass):
    if issubclass(klass, base.GLTypes) and klass != base.GLTypes:
        print create_class_doc(klass)

