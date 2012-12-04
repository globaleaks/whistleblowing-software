from globaleaks.rest.api import spec
from globaleaks.messages import base
from utils import cleanup_docstring
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
        print resource[0]
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
        print key

        for method, text in value.iteritems():

            print "\t", method

            lines = text.split("\n")
            wikidoc.add_h3("%s %s" % (method.upper(), key ))

            for line in lines:

                request_i = line.find('Request:')
                answer_i = line.find('Answer:')
                error_i = line.find('Errors:')
                param_i = line.find('Parameter:')

                if request_i != -1:
                    wikidoc.add_request(get_request(line[request_i:]))
                elif answer_i != -1:
                    wikidoc.add_answer(get_answer(line[answer_i:]))
                elif error_i != -1:
                    wikidoc.add_error(get_errors(line[error_i:]))
                elif param_i != -1:
                    wikidoc.add_param(get_param(line[param_i:]))
                else:
                    wikidoc.add_line(line)


class reStructuredText:

    def __init__(self):
        self.collected = ''

    def add_h3(self, text):
        text = text.strip("\n")
        self.collected += text + "\n"
        for i in range(0, len(text)):
            self.collected += '-'
        self.collected += "\n\n"

    def add_h2(self, text):
        text = text.strip("\n")
        self.collected += text + "\n"
        for i in range(0, len(text)):
            self.collected += '='
        self.collected += "\n\n"

    def add_request(self, reqname):
        self.collected += reqname + "\n"

    def add_answer(self, answname):
        self.collected += answname + "\n"

    def add_error(self, errorname):
        self.collected += errorname + "\n"

    def add_param(self, paramname):
        self.collected += paramname + "\n"

    def add_line(self, linestuff):
        self.collected += linestuff + "\n"

if __name__ == '__main__':

    wikidoc = reStructuredText()
    fill_doctree()

    travel_over_tree(wikidoc, 'U')
    travel_over_tree(wikidoc, 'R')
    travel_over_tree(wikidoc, 'T')
    travel_over_tree(wikidoc, 'A')

    with file("APIdocGenerated.reST", 'w+') as f:
        f.write(wikidoc.collected)

