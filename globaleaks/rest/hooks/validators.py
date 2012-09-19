"""
Validator perform intetrigy checks in the submitted field,
and perform every sanity checks in the submitted type
it may perform loggin for specific operation if enabled.

Validator DO NOT PERFORM logical checks, in example, if
only a receiver can express pertinencies in a Tip, this 
would be answered by the Tip object.

If one of the:
    is_$type() function return False
    (see at the end of th file)
than the expected type is wrong, and an exception is raise.
"""

class SubmissionValidator(object):
    @classmethod
    def validate(*args, **kw):
        print "Submission you're validate ", args, kw
        return True

    @classmethod
    def files(*args, **kw):
        print "Submission (files) you're validate ", args, kw
        return True

class TipValidator(object):
    @classmethod
    def validate(*args, **kw):
        print "Tip you're validate ", args, kw

        return True

class ReceiverValidator(object):
    @classmethod
    def validate(*args, **kw):
        print "Receiver you're validate ", args, kw
        return True

class AdminValidator(object):
    @classmethod
    def validate(*args, **kw):
        print "Admin you're validate ", args, kw
        return True

class NodeValidator(object):
    @classmethod
    def validate(*args, **kw):
        print "Node, a GET without parameter, is valid"
        return True


"""
Regular expressions validator functions
"""

"""
Check if is a number and positive and with max 10 digits
"""
def is_positive(value):
    return True

# well this need to be converted in unicode before ?
def is_string(value):
    return True

# expect a 32bit format date
def is_date(value):
    return True

# checks between the module enumeration
def is_moduleType(value):
    return True

