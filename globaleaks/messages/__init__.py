__all__ = ['base']
from . import base

from globaleaks.messages.errors import GLTypeError
from globaleaks.messages.base import SpecialType, GLTypes

import json

def validateType(value, validType):
    if type(value) is validType:
        return
    else:
        raise GLTypeError("%s must be of %s type. Got %s instead" % (value, validType, type(value)))

def validateGLType(value, glType):
    message = json.dumps(value)
    validateMessage(message, glType)

def validateSpecialType(value, specialType):
    """
    Validate a special type that is not in the standard types (int, str,
    unicode, etc.)
    """
    specialType.validate(value)

def validateItem(val, validType):
    """
    Takes as input an object and a type that it should match and raises an
    error if it does not match the type it is supposed to be.

    If there is still some processing to do it will call itself of
    validateMessage recursively to validate also the sub-elements.

    val: value to be to validated. This is a python object.

    validType: a subclass of GLTypes, SpecialType, type or list. This is what
    val should look like.
    """
    if type(validType) is list:
        if not type(val) is list:
            raise GLTypeError("%s must be of type list" % val)
        valid = validType[0]
        for item in val:
            if type(item) is dict:
                validateGLType(item, valid)
            else:
                validateItem(item, valid)

    elif issubclass(validType, SpecialType):
        validType = validType()
        validType.validate(val)

    elif issubclass(validType, GLTypes):
        validateGLType(val, validType)

    elif type(validType) is type:
        validateType(val, validType)

    else:
        raise GLTypeError("Invalid type specification")

def validateMessage(message, messageType):
    """
    Takes a string that represents a JSON messages and checks to see if it
    conforms to the message type it is supposed to be.

    This message must be either a dict or a list. This function may be called
    recursively to validate sub-parameters that are also go GLType.

    message: the message string that should be validated

    messageType: the GLType class it should match.
    """
    messageSpec = messageType()

    obj = json.loads(message)
    if type(obj) is list:
        obj = obj.pop()
    elif type(obj) is not dict:
        raise Exception("Message is not in dict format")

    for k, val in obj.items():
        try:
            validType = messageSpec[k]
        except:
            raise GLTypeError("Specified field is not supported."
                              "could not find %s in message spec" % k)

        validateItem(val, validType)

def validateWith(fn):
    """
    This is a decorator that does validation of the content in
    self.request.body and makes sure it is of the correct messageType.
    """
    def decorator(self, messageType):
        print "Validating"
        print self.request.body
        validateMessage(self.request.body, messageType)
        fn(self)
    return decorator

