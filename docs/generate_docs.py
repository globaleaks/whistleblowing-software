from globaleaks.rest.api import spec
from globaleaks.messages import base
from globaleaks.messages import requests
from globaleaks.messages import responses
from utils import cleanup_docstring
import inspect
import sys, string


doctree = {}
URTA_map = {}

# doctree is the dict containing the API spec
#   the keys of this dict are the API PATH + URTA code
#   the item of the API path is another dict
#       the keys of this dict are the methods supported
#       the item of this key is an array with the collected info from the docstring

typestree = {}

# typestree is the dict containing the data types description and content


def pop_URTA(descriptionstring):

    descinlist = descriptionstring.split("\n")
    if descinlist[0] == '' and len(descinlist[1]) == 2:
        descinlist.pop(0)
        URTA = descinlist.pop(0)
        cleandesc = string.join(descinlist)
    else:
        return False


    if len(URTA) == 2 and len(cleandesc) > 10:
        return (URTA, cleandesc)
    else:
        return False

def fill_doctree():

    for resource in spec:

        # static file handler, not managed here:
        if resource[0] == "/(.*)":
            continue

        handler = resource[1]

        if handler.__doc__ is None:
            print "Missing class docstring in Handler class:", resource[0]
            quit()

        classdoc = cleanup_docstring(handler.__doc__)

        URTA_combo = pop_URTA(classdoc)
        if not URTA_combo:
            print "missing URTA code and description in class: %s (%s)" % (resource[0], resource[1])
            quit()

        # URTA_combo is an array of ( URTA, description )
        URTA_map.update({ resource[0] : URTA_combo  })
        doctree.update({resource[0]: {} })

        handler_child = {}
        for method in ['get', 'post', 'put', 'delete']:
            m = getattr(handler, method)
            if m.__doc__:
                docstring = cleanup_docstring(m.__doc__)
                handler_child.update({method : docstring})

        doctree.update({ resource[0] : handler_child })

    return doctree


def get_request(partial_line):
    return partial_line.strip(" ,")

def get_answer(partial_line):
    return partial_line

def get_errors(partial_line):
    return partial_line

def get_param(partial_line):
    return partial_line

def travel_over_tree(wikidoc, URTAindex=None):

    for key, value in doctree.iteritems():

        if URTAindex and URTA_map.get(key)[0][0] != URTAindex[0]:
            continue

        wikidoc.add_h2(key)
        print "processing API: ", key

        for method, text in value.iteritems():

            print "\t", method.upper()

            lines = text.split("\n")
            wikidoc.add_h3("%s %s" % (method.upper(), key), text)

            matrix = [
                  [ wikidoc.add_response, 'Response:', False],
                  [ wikidoc.add_error, 'Errors:', False ],
                  [ wikidoc.add_request, 'Request:', False],
                  [ wikidoc.add_param, 'Parameter:', False ]
                ]

            # for each line, check one of the keyword above, and
            # use the appropriate method in wikidoc.
            for line in lines:

                parsed_correctly = False
                for ndx, entry in enumerate(matrix):

                    x_i = line.find(entry[1])
                    if x_i != -1:
                        index = x_i + len(entry[1]) + 1
                        entry[0](get_request(line[index:]))
                        parsed_correctly = True
                        matrix[ndx][2] = True


                if not parsed_correctly:
                    wikidoc.add_line(line)

            if method.upper() == 'GET':
                if not matrix[0][2] or not matrix[1][2]:
                    print "Missing Response/Error"
                    quit()
            else:
                if not matrix[0][2] or not matrix[1][2] or not matrix[2][2]:
                    print "Missing Request/Response/Error"
                    quit()


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


def handle_klass_entry(source, name, klass):

    if issubclass(klass, base.GLTypes) and klass != base.GLTypes:
        types_doc = create_class_doc(klass)
        print "Complex ", source, ":\n", types_doc
    elif issubclass(klass, base.SpecialType) and klass != base.SpecialType:
        special_doc = create_special_doc(klass)
        print "Special ", source, ":\n", special_doc


class reStructuredText:

    def __init__(self):
        self.collected = ''

    def add_h3(self, title, text):
        title = title.strip("\n")
        self.collected += title + "\n"
        for i in range(0, len(title)):
            self.collected += '-'
        self.collected += "\n\n"
        self.collected += text + "\n"

    def add_h2(self, text):
        text = text.strip("\n")
        self.collected += text + "\n"
        for i in range(0, len(text)):
            self.collected += '='
        self.collected += "\n\n"

    def add_entrylist(self, error, answer, request=None, param=None):
        pass

    def add_request(self, reqname):
        self.collected += reqname + "\n"

    def add_response(self, answname):
        self.collected += answname + "\n"

    def add_error(self, errorname):
        self.collected += errorname + "\n"

    def add_param(self, paramname):
        self.collected += paramname + "\n"

    def add_line(self, linestuff):
        self.collected += linestuff + "\n"

    for name, klass in inspect.getmembers(base, inspect.isclass):
        handle_klass_entry('base', name, klass)
    for name, klass in inspect.getmembers(requests, inspect.isclass):
        handle_klass_entry('requests', name, klass)
    for name, klass in inspect.getmembers(responses, inspect.isclass):
        handle_klass_entry('responses', name, klass)

if __name__ == '__main__':
    import datetime

    wikidoc = reStructuredText()
    fill_doctree()

    travel_over_tree(wikidoc, 'U')
    travel_over_tree(wikidoc, 'R')
    travel_over_tree(wikidoc, 'T')
    travel_over_tree(wikidoc, 'A')

    newstring = "This is an autogenerated file based on **docs/generate_docs.py**.\n"+\
                "The script looks in the docstrings inside of the Handlers Class"+\
                " and Method implementations\n\nThis version has been generated"+\
                " in: %s\n\n.. contents:: Table of Contents\n\n%s" % \
                (datetime.date.today(), wikidoc.collected )

    wikidoc.collected = newstring

    with file("APIdocGenerated.reST", 'w+') as f:
        f.write(wikidoc.collected)


