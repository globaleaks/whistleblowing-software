import json
import os

def diff(func):

    def wrapper(self, v):
        values = getattr(self, "_values")

        import pdb
        #pdb.set_trace()
        if type(values.get(func.__name__)) == type(0) and values.get(func.__name__) == 0:
            print "field change " + func.__name__ + " = " + str(v) + " was: " + str(values.get(func.__name__))
        elif type(values.get(func.__name__)) == type('') and values.get(func.__name__) == '':
            print "field change " + func.__name__ + " = " + v + " was: " + values.get(func.__name__) 
        else:
            print "field set" + func.__name__ + ' = ' + v

        # finally lanch the RestJSONwrapper.function, having
        # kept only 'readonly' operation in the _variables
        func(self, v)

    return wrapper

class RestJSONwrapper:

    def __init__(self):
        print "error: never invoke " + self.__class__


class FileRest(RestJSONwrapper):

    def __init__(self, filename):
        self._values = dict({
            'filename' : '', 'comment' : '', 'content_type' : '',
            'size' : 0, 'date' : 0, 'metadata' : 0
        })

        self._comment = self._content_type = ''
        self._size = self._mod_time = self._clean = 0

        self._filename = filename
        self._values['filename'] = filename

    @diff
    def content_type(self, v):
        self._values['content_type'] = v

    @diff
    def size(self, v):
        self._values['size'] = v

    @diff
    def time(self, v):
        self._values['time'] = v

    @diff
    def comment(self, v):
        self._values['comment'] = v

    @diff
    def metadata(self, v):
        self._values['metadata'] = v

    def printJSON(self):
        if not self._values['size'] or not self.value['time']:
            statinfo = os.stat(self._filename)
            self._values['size'] = statinfo.st_size
            self._values['date'] = statinfo.st_mtime

        for key, value in self._values.items():
            if type(value) == type(' ') and value == '':
                print "missing text field in " + key
            elif type(value) == type(1) and value == 0:
                print "missing int field in " + key
            else:
                print "invalid field type in: " + key + " = " + str(value)

        import sys
        json.dump(self._values, sys.stdout)
        print "\n"



# test

mineuse = FileRest("/etc/passwd")
mineuse.comment("This is an extremely sensitive document")
mineuse.content_type("text/plain")
mineuse.content_type("text/html")
mineuse.metadata(1)
mineuse.printJSON()


