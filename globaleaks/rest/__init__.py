__all__ = [ 'api', 'base', 'requests', 'responses', 'errors']

from . import base
from . import requests
from . import responses
from . import errors
from . import api

from globaleaks.messages.errors import GLTypeError
from globaleaks.messages.base import SpecialType, GLTypes

import json

def validateType(value, valid_type):
    if type(value) is valid_type:
        return
    else:
        raise GLTypeError("%s must be of %s type. Got %s instead" % (value, valid_type, type(value)))

def validateGLType(value, gl_type):
    message = json.dumps(value)
    validateMessage(message, gl_type)

def validateSpecialType(value, specialType):
    """
    Validate a special type that is not in the standard types (int, str,
    unicode, etc.)
    """
    specialType.validate(value)

def validateItem(val, valid_type):
    """
    Takes as input an object and a type that it should match and raises an
    error if it does not match the type it is supposed to be.

    If there is still some processing to do it will call itself of
    validateMessage recursively to validate also the sub-elements.

    val: value to be to validated. This is a python object.

    valid_type: a subclass of GLTypes, SpecialType, type or list. This is what
    val should look like.
    """
    if type(valid_type) is list:
        if not type(val) is list:
            raise GLTypeError("%s must be of type list" % val)
        valid = valid_type[0]
        for item in val:
            if type(item) is dict:
                validateGLType(item, valid)
            else:
                validateItem(item, valid)

    elif issubclass(valid_type, SpecialType):
        valid_type = valid_type()
        valid_type.validate(val)

    elif issubclass(valid_type, GLTypes):
        validateGLType(val, valid_type)

    elif type(valid_type) is type:
        validateType(val, valid_type)

    else:
        raise GLTypeError("Invalid type specification")

def validateMessage(message, message_type):
    """
    Takes a string that represents a JSON messages and checks to see if it
    conforms to the message type it is supposed to be.

    This message must be either a dict or a list. This function may be called
    recursively to validate sub-parameters that are also go GLType.

    message: the message string that should be validated

    message_type: the GLType class it should match.
    """
    messageSpec = message_type()

    obj = json.loads(message)
    if type(obj) is list:
        obj = obj.pop()
    elif type(obj) is not dict:
        raise GLTypeError("Message is not in dict format")

    for k, val in obj.items():
        try:
            valid_type = messageSpec[k]
        except:
            raise GLTypeError("Messagge validation fail: missing field %s" % k)

        validateItem(val, valid_type)

    return obj

def validateWith(fn):
    """
    This is a decorator that does validation of the content in
    self.request.body and makes sure it is of the correct message_type.
    """
    def decorator(self, message_type):
        print "Validating"
        print self.request.body
        validateMessage(self.request.body, message_type)
        fn(self)
    return decorator

