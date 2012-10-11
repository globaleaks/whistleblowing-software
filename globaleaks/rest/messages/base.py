# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.
import inspect
from datetime import datetime
import json

from globaleaks.rest.messages.errors import *

## TODO of the file:
# - aquired
# - comparation of structure

class GLTypes(dict):
    """
    Types is a module supporting the recurring types format in JSON
    communications. It's documented in
    https://github.com/globaleaks/GlobaLeaks/wiki/recurring-data-types

    This class is used whenever a RESTful interface need to manage
    an input element or an output element.

    The recurring elements in GLBackend, researched here:
    https://github.com/globaleaks/GLBackend/issues/14
    and documented in https://github.com/globaleaks/GlobaLeaks/wiki/recurring-data-types
    are instances based on GLTypes
    """
    specification = {}
    def __getitem__(self, key):
        return self.specification[key]

    def __setitem__(self, key, val):
        self.specification[key] = val

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
            raise GLTypeError("Not supported field")

        validateItem(val, validType)


class SpecialType(object):
    def validate(self, data):
        pass

class dateType(SpecialType):
    pass

class timeType(SpecialType):
    pass

class folderID(SpecialType):
    pass

class receiverID(SpecialType):
    pass

class moduleID(SpecialType):
    pass

class moduleENUM(SpecialType):
    pass

class contextID(SpecialType):
    pass

class commentENUM(SpecialType):
    pass

class tipID(SpecialType):
    pass

class fileDict(GLTypes):
    specification = {"filename": unicode,
                "file_description": unicode,
                "size": int,
                "content_type": unicode,
                "date": dateType,
                "cleaned_meta_data": bool,
                "completed": bool
                }

class folderDict(GLTypes):
    specification = {"fID": folderID,
            "folder_name": unicode,
            "folder_description": unicode,
            "download_performed": int,
            "files": [fileDict],
            }
            # this information is comunicated along the
            # folderDict, also if tracked in the TipReceiver
            # table. this is useful because some Folder would not be
            # downloadable when other are.

class receiverDescriptionDict(GLTypes):
    specification = {"rID": receiverID,
            "can_delete_submission": bool,
            "can_postpone_expiration": bool,
            "can_configure_notification": bool,
            "can_configure_delivery": bool,
            # -----------------------------------------
            "can_trigger_escalation": bool,
            "receiver_level": int,
            # remind: both of them need to be specified
            "receiver_name": unicode,
            "receiver_description": unicode,
            "receiver_tags": unicode,
            # verify - is it specified ?
            "creation_date": timeType,
            "last_update_date": timeType,
            # update the name
            "language_supported": [unicode],
            }
class nodePropertiesDict(GLTypes):
    """
    Gradually this options has been shrinked because:
        1) threat model need to be completed
        2) some of them has been moved in the Contexts
        3) CBP are aimed in leakdirectory integration
    """
    specification = {"anonymous_submission_only": bool}

class adminStatisticsDict(GLTypes):
    """
    This containers need to be defined, IMHO would be an aggregate
    of information collected about the latest X-hours of the node
    and so far
    """
    specification = {"hours_interval": int,
            "download_number": int,
            "receiver_accesses": int,
            "submission_received": int}

class publicStatisticsDict(GLTypes):
    """
    The following container is used for the public statistic,
    collected by site that perform uptime and/or measurement,
    or readed by users.
    Need to be defined, depends what's is considered to be
    harmless for node life, and what's can be easily collected
    """
    specification = {"active_contexts": int,
            "active_receivers": int,
            "uptime_days": int}


class formFieldsDict(GLTypes):
    """
    field_type need to be defined as ENUM, in the future,
    and would be the set of keyword supported by the
    client (text, textarea, checkbox, GPS coordinate)
    """
    specification = {"presentation_order": "int",
            "label": unicode,
            "name": unicode,
            "required": bool,
            "hint": unicode,
            "value": unicode,
            "type": unicode}


class moduleDataDict(GLTypes):
    specification = {"mID": moduleID,
            "active": bool,
            "module_type": moduleENUM,
            "name": unicode,
            "module_description": unicode,
            "service_message": unicode,
            "admin_options": [formFieldsDict],
            "user_options": [formFieldsDict]}


class contextDescriptionDict(GLTypes):
    """
    fields: one or more, but almost one field is needed

    selectable_receiver:
        update, the previous flag before was documented as
        node-wise configuration, now is context-wise

    receivers: properties in Receiver element

    language_supported: it's the collection of Language from 'receivers'
    """
    specification = {"c_id": contextID,
            "name": unicode,
            "context_description": unicode,
            "creation_date": timeType,
            "update_date": "time",
            "fields": [formFieldsDict()],
            "selectable_receiver": bool,
            "receivers": [receiverDescriptionDict],
            "escalation_threshold": int,
            "language_supported": unicode}

class commentDescriptionDict(GLTypes):
    specification = {"writtentext": unicode,
            "commenttype": commentENUM,
            "author": unicode,
            "date": timeType}


class tipSubIndex(GLTypes):
    specification = {"tID": tipID,
            "tip_title": unicode,
            "notification_adopted": unicode,
            "delivery_adopted": unicode,
            "download_limit": int,
            # remind: download_performed is inside the folderDict
            "access_limit": int,
            "access_performed": int,
            "expiration_date": timeType,
            "creation_date": timeType,
            "last_update_date": timeType,
            "comment_number": int,
            "folder_number": int,
            "overall_pertinence": int}

class tipIndexDict(GLTypes):
    """
    Remind, this Tip access is different for every receiver,
    Remind: this object is the LIST OF ACTIVE TIP, does not
    cover the content.
    """
    specification = {"cID": contextID,
            "tiplist": [tipSubIndex]}

class tipDetailsDict(GLTypes):
    """
    This element contain mostly of the descriptive information
    of the Tip
    """

    """
    What's follow are the details Tip dependent
    """
    specification = {"tip": tipSubIndex,
            "tip_data": formFieldsDict,
            "folder": folderDict,
            "comment": commentDescriptionDict,
            "receiver_selected": receiverDescriptionDict}


class localizationDict(GLTypes):
    """
    This object would be implemented when localization would be solved
    as issue: https://github.com/globaleaks/GLBackend/issues/18
    """
    specification = {}

