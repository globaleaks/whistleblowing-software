import json
import os

def diff(func):

    def wrapper(self, v):
        print "checking: '_" + func.__name__ + "'" 
        values = getattr(self, "_values")
        print values['filename'] + " yay " + values[func.__name__]

        if values.has_key(func.__name__):
            print "beh ?" + values.get(func.__name__) + values.get('filename')

        if hasattr(self, '_' + func.__name__):
            if not getattr(self, '_' + func.__name__) == 'v':
                print "field value change [" + func.__name__ + "] from: '" + getattr(self, '_' + func.__name__) + "' to '" + v  + "'"
        else:
            print "missing requested attr based on function name " + func.__name__

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
        self._content_type = v
        print 'a' + self.__name__
        self._values[self.__name__] = v

    @diff
    def size(self, v):
        self._size = v
        self._values[self.__name__] = v

    @diff
    def time(self, v):
        self._time = v
        self._values[self.__name__] = v

    @diff
    def comment(self, v):
        self._comment = v
        print dir(self)
        print self
        import pdb
        pdb.set_trace()
        print self.__name__
        self._values[self.__name__] = v

    @diff
    def metadata(self, v):
        self._clean = v
        self._values[self.__name__] = v

    def printJSON(self):
        if not self._size or not self._mod_time:
            statinfo = os.stat(self._filename)
            self._size = statinfo.st_size
            self._mod_time = statinfo.st_mtime

        if self._content_type == '' or self._comment == '' or self._clean == 0:
            print "missing field"

        obj4json = dict({ 
            'filename' : self._filename,
            'comment' : self._comment,
            'size' : self._size,
            'content_type' : self._content_type,
            'date' : self._mod_time,
            'CleanedMetaData' : self._clean })

        import sys
        json.dump(obj4json, sys.stdout)
        print "\n"


# test

mineuse = FileRest("/etc/passwd")
mineuse.comment("This is an extremely sensitive document")
mineuse.content_type("text/plain")
mineuse.content_type("text/html")
mineuse.CleanMetaData(1)
mineuse.printJSON()


