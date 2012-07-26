import json
import os

class RestJSONwrapper:

    def __init__(self):
        print "error: never invoke " + self.__class__

    # XXX grok decorators TODO
    def diff(self):
        pass


class FileRest(RestJSONwrapper):

    """
    _obj = dict({
            'filename' : '',
            'comment' : '',
            'size' : 0,
            'content_type' :  '',
            'date' : 0,
            'CleanedMetaData' : 0
    """

    def __init__(self, filename):
        self._comment = self._content_type = ''
        self._size = self._mod_time = self._clean = 0

        self._filename = filename

    def content_type(self, v):
        self._content_type = v

    def size(self, v):
        self._size = v

    def time(self, v):
        self._time = v

    def comment(self, v):
        self._comment = v

    def CleanMetaData(self, v):
        self._clean = v

    def printJSON(self):
        if not self._size or not self._mod_time:
            statinfo = os.stat(self._filename)
            self._size = statinfo.st_size
            self._mod_time = statinfo.st_mtime

        if self._content_type == '' or self._comment == '':
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


# test

mineuse = FileRest("/etc/passwd")
mineuse.content_type("text/plain")
mineuse.comment("This is an extremely sensitive document")
mineuse.CleanMetaData(1)
mineuse.printJSON()


