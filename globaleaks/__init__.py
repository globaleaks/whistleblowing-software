"""
    GLBackend
    *********

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""
__all__ = [ 'core', 'rest', 'modules', 'utils', 'backend']

class DummyHandler:
    handler = None
    def __getattr__(self, name, *arg, **kw):
        def dummy_func(*arg, **kw):
            return {'arg': arg, 'kw': kw}
        return dummy_func

class Processor(object):
    """
    Base class for processing requests from the GlobaLeaks Backend API.

    A processor should define methods that are named like all the action
    variable passed from api.py.
    For example if we want to handle /foo/bar and /foo/bar2 we will define this
    in api.py like so:

            [(r'/foo/bar', fooHandler,
            dict(action='bar',
                 supportedMethods=['POST', 'GET'])),
            (r'/foo/bar2',
            dict(action='bar2',
                 supportedMethods=['POST']))]

    I will then define in a Processor subclass the methods bar and bar2.

    If I am interested in implementing validation and sanitization of the
    client supplied arguments I will also define

    barValidate
    barSanitize

    and

    bar2Validate
    bar2Sanitize

    the handler attribute will point to the cyclone RequestHandler, allowing
    the extraction of the request headers and everything that is stored in the
    RequestHandler from the Processor class.
    """
    handler = None

