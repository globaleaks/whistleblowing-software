from globaleaks.rest import requests, responses, errors, base
import inspect
import string

doctree = []

def shooter_list_dump():

    # 'U2_GET':'GET_/submission/@CID@/new',#U2

    with file("shooter.include", 'w+') as f:

        for k,v in URTA_map.iteritems():
            for method, desc in doctree.get(k).iteritems():
                f.write("'%s_%s':'%s_%s',\n" % ( v[0], method.upper(), method.upper(), k ) )



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
    """
    This function read all the code and extract the docstring,
    is collected with this format:

    Output struct that we want generated:

    {
        'API' : "/node" # API contain the API path, with regexp inside, if happen
        'shortname': A1|U1|T1 # short name usable from command line tool
        'class_doc': Class docstring (a sort of brief)
        'GET': true|false
        'POST: true|false # a boolean aiming if a method is supported or not, this trigger the
        next four entry:
        'GET_request': messageType # if a method is supported, the message type
        'GET_response': messageType # as before
        'GET_error': [ errors ] # possible output errors
        'GET_param' : parameters
        'GET_docstring': documentation about GET role for the API
    }

    Every entry is put in a list.
    @return: a list with the previously explained format.
    """
    from globaleaks.rest.api import spec

    doctree = []

    for resource in spec:

        doc_entry = {}

        # static file handler, not managed here:
        if resource[0] == "/(.*)":
            continue

        doc_entry.update({'API' : resource[0]}) # the API /path/with/regexp
        handler_class = resource[1]

        if handler_class.__doc__ is None:
            print "Missing class docstring in Handler class:", resource[0]
            quit()

        raw_class_doc =  cleanup_docstring(handler_class.__doc__)

        URTA_combo = pop_URTA(raw_class_doc)
        # URTA_combo is an array of ( shortname, description )

        if not URTA_combo:
            print "missing URTA code and description in: %s, class: %s" % (resource[0], resource[1])
            quit()

        doc_entry.update({'shortname' : URTA_combo[0]})
        doc_entry.update({'class_doc' : URTA_combo[1]})

        for method in ['GET', 'POST', 'PUT', 'DELETE']:

            m = getattr(handler_class, method.lower())

            if m.__doc__:

                doc_entry.update({method: True})

                raw_docstring = cleanup_docstring(m.__doc__)

                matrix = [
                    [ "response", 'Response:'],
                    [ "error", 'Errors:' ],
                    [ "request", 'Request:'],
                    [ "param", 'Parameter:']
                ]

                for line in raw_docstring.split("\n"):

                    for x in matrix:
                        if line.find(x[1]) != -1:
                            docvalues = (line.split(x[1]))[1]
                            doc_entry.update({"%s_%s" % ( method, x[0]) : docvalues })

                doc_entry.update({"%s_docstring" % method : "\n\n".join(raw_docstring.split("\n\n")[1:])})

        doctree.append(doc_entry)

    import json
    print(json.dumps(doctree, indent=4))

    return doctree

def cleanup_docstring(docstring):
    doc = ""
    stripped = [line.strip() for line in docstring.split("\n")]
    doc += '\n'.join(stripped)
    return doc

def get_elementNames(partial_line):
    return partial_line.replace(" ", '').split(",")

def travel_over_tree(wikidoc, URTAindex, intro):

    wikidoc.add_h1(intro)

    for doc_entry in doctree:

        if doc_entry['shortcode'] != URTAindex[0]:
            continue

        wikidoc.add_h2(doc_entry['API'])
        wikidoc.collected += "\n" + doc_entry['class_doc']

        
        if doc_entry.has_key('GET') and doc_entry['GET']:




def create_spec(rec, spec):
    doc = ""

    if type(spec) == type([]):

        this_rec = rec + 1
        for element in spec:
            doc += "is List of elements:\n"
            doc += create_spec(this_rec, element)

    elif type(spec) == type({}):

        for k, v in spec.items():
            if type(v) == type([]):
                doc += "list %s" % k
            else:
                doc += k + "\n"
                doc += "%s\n" % handle_klass_entry(rec + 1, v)
                # doc += "    %s: %s\n" % (k, v)
    else:

        doc += "\ndoc of a type: %s" % spec

    return doc

def create_class_doc(rec, klass):
    doc = "\n`%s`_\n\n" % klass.__name__
    if klass.__doc__:
        cleanup_docstring(klass.__doc__)
    doc += "\n"
    doc += create_spec(rec +1, klass.specification)
    doc += "\n\n"
    return doc

def create_special_doc(klass):
    doc = "\n`%s`_\n%s\n" % (klass.__name__, klass.regexp)
    return doc


def handle_klass_entry(rec, klass):

    if issubclass(klass, base.GLTypes) and klass != base.GLTypes:
        types_doc = create_class_doc(rec, klass)
        for x in range(0, rec):
            types_doc ="\t" + types_doc
        return types_doc
    elif issubclass(klass, base.SpecialType) and klass != base.SpecialType:
        special_doc = create_special_doc(klass)
        for x in range(1, rec):
            special_doc ="\t" + special_doc
        return special_doc

def handle_errortype_entry(errorklass):

    if issubclass(errorklass, errors.GLException):
        return errorklass.__doc__

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

    def add_request(self, reqname):

        if typestree.has_key(reqname):
            self.collected += typestree[reqname] + "\n"
            return True

        typedesc = None
        if reqname == "Unknown":
            typedesc = "Unknown"
        elif reqname == "None":
            typedesc = "None"
        else:
            for name, klass in inspect.getmembers(requests, inspect.isclass):
                if name == reqname:
                    print "requests match", name
                    typedesc = handle_klass_entry(1, klass)
                    break

            if typedesc is None or typedesc == "":
                print "Missing description of requests", reqname,
                return False

        typestree.update({reqname : typedesc })
        self.collected += "`" + reqname + "`:" + typedesc + "\n"
        return True


    def add_response(self, responame):

        if typestree.has_key(responame):
            self.collected += typestree[responame] + "\n"
            return True

        typedesc = None
        if responame == "Unknown":
            typedesc = "Unknown"
        elif responame == "None":
            typedesc = "None"
        else:
            for name, klass in inspect.getmembers(responses, inspect.isclass):
                if name == responame:
                    #import pdb
                    #pdb.set_trace()
                    typedesc = handle_klass_entry(1, klass)
                    break

            if typedesc is None or typedesc == "":
                print "Missing description of responses", responame,
                return False

        typestree.update({responame : typedesc })
        self.collected += "`" + responame + "`:" + typedesc + "\n"
        return True


    def add_error(self, errorname):

        if typestree.has_key(errorname):
            self.collected += typestree[errorname] + "\n"
            return True

        typedesc = None
        if errorname == "Unknown":
            typedesc = "Unknown"
        elif errorname == "None":
            typedesc = "None"
        else:
            for name, klass in inspect.getmembers(errors, inspect.isclass):
                if name == errorname:
                    typedesc = handle_errortype_entry(klass)
                    break

            if typedesc is None:
                print "Missing description of GLException:", errorname,
                return False

        typestree.update({errorname: typedesc })
        self.collected += "`" + errorname + "`:" + typedesc + "\n"
        return True


    def add_param(self, paramname):
        self.collected += "Parameter NotYetSupported: " + paramname + "\n"
        return True

    def add_line(self, linestuff):
        self.collected += linestuff + "\n"

if __name__ == '__main__':
    import datetime

    wikidoc = reStructuredText()
    fill_doctree()

    travel_over_tree(wikidoc, 'U', "Unauthenticated API")
    travel_over_tree(wikidoc, 'R', "Receiver API")
    travel_over_tree(wikidoc, 'T', "Tip API")
    travel_over_tree(wikidoc, 'A', "Administrative API")
    travel_over_tree(wikidoc, 'D', "Debug API")

    newstring = "This is an autogenerated file based on **docs/generate_docs.py**.\n"+\
                "The script looks in the docstrings inside of the Handlers Class"+\
                " and Method implementations\n\nThis version has been generated"+\
                " in: %s\n\n.. contents:: Table of Contents\n\n%s" % \
                (datetime.date.today(), wikidoc.collected )

    wikidoc.collected = newstring

    with file("APIdocGenerated.reST", 'w+') as f:
        f.write(wikidoc.collected)

    # dump API list in shooter.py format
    shooter_list_dump()


