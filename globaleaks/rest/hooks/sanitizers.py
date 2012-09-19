"""
Sanitizer goals: every field need to be checked, escaped
if something is wrong in format, raise an exception

(what I wish but....? 
 If a string is present, sanitize every possibile escape sequence
)

XXX

I've make an extensive research of generic module for python securty
actualy I've found:
https://github.com/django/django/blob/master/django/template/defaultfilters.py
(But is part of Django, we can import that)
some checks in simplejson module:
http://code.google.com/p/simplejson/source/browse/tags/simplejson-2.1.1/simplejson/encoder.py#287

Actually I've not found a reliable security module for sanitize and checks fields in JSON
"""


class SubmissionSanitizer(object):
    @classmethod
    def sanitize(glbh, request):
        return request

    @classmethod
    def files(glbh, request):
        return request

class TipSanitizer(object):
    @classmethod
    def sanitize(glbh, request):
        return request

class ReceiverSanitizer(object):
    @classmethod
    def sanitize(glbh, request):
        return request

class AdminSanitizer(object):
    @classmethod
    def sanitize(glbh, request):
        return request

