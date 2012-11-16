# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.
import inspect
import json
from datetime import datetime
from globaleaks.messages.errors import *

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

    def __call__(self):
        return self.specification


class SpecialType(object):
    regexp = ""
    def validate(self, data):
        import re
        if re.match(self.regexp, data):
            return
        else:
            raise GLTypeError("%s does not match %s" % (data, self.regexp))

class dateType(SpecialType):
    pass

class timeType(SpecialType):
    pass

class folderGUS(SpecialType):
    regexp = r"(f_[a-zA-Z]{20,20})"

# XXX not true anymore, need to be update the specification and the glossary
class receiptGUS(SpecialType):
    regexp = r"(\d{10,10})"

class submissionGUS(SpecialType):
    regexp = r"(s_[a-zA-Z]{50,50})"

class receiverGUS(SpecialType):
    regexp = r"(r_[a-zA-Z]{20,20})"

class moduleGUS(SpecialType):
    regexp = r"(m_\d{10,10})"

class moduleENUM(SpecialType):
    regexp = "(notification|delivery|inputfilter)"

class contextGUS(SpecialType):
    regexp = r"(c_[a-zA-Z]{20,20})"

class commentENUM(SpecialType):
    regexp = r"(receiver|system|whistleblower)"

class tipGUS(SpecialType):
    regexp = r"(t_[a-zA-Z]{50,50})"

class fileDict(GLTypes):
    specification = {"name": unicode,
                "description": unicode,
                "size": int,
                "content_type": unicode,
                "date": dateType,
                "metadata_cleaned": bool,
                "completed": bool
                }

class folderDict(GLTypes):
    specification = {"gus": folderGUS,
            "name": unicode,
            "description": unicode,
            "downloads": int,
            "files": [fileDict],
            }
            # this information is comunicated along the
            # folderDict, also if tracked in the TipReceiver
            # table. this is useful because some Folder would not be
            # downloadable when other are.

class receiverDescriptionDict(GLTypes):
    specification = {"gus": receiverGUS,
            "can_delete_submission": bool,
            "can_postpone_expiration": bool,
            "can_configure_notification": bool,
            "can_configure_delivery": bool,
            # -----------------------------------------
            "can_trigger_escalation": bool,
            "receiver_level": int,
            # remind: both of them need to be specified
            "name": unicode,
            "description": unicode,
            "tags": unicode,
            # verify - is it specified ?
            "creation_date": timeType,
            "last_update_date": timeType,
            # update the name
            "languages_supported": [unicode],
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
    specification = {"gus": moduleGUS,
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
    specification = {"context_gus": contextGUS,
            "name": unicode,
            "description": unicode,
            "creation_date": timeType,
            "update_date": timeType,
            "fields": [formFieldsDict()],
            "selectable_receiver": bool,
            "receivers": [receiverDescriptionDict],
            "escalation_threshold": int,
            "languages_supported": [unicode]}

class commentDescriptionDict(GLTypes):
    specification = {"writtentext": unicode,
            "commenttype": commentENUM,
            "author": unicode,
            "date": timeType}


class tipSubIndex(GLTypes):
    specification = {"tip_gus": tipGUS,
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
    specification = {"context_gus": contextGUS,
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
            "fields": formFieldsDict,
            "folders": [folderDict],
            "comments": commentDescriptionDict,
            "context": contextDescriptionDict,
            "receivers": receiverDescriptionDict}


class localizationDict(GLTypes):
    """
    This object would be implemented when localization would be solved
    as issue: https://github.com/globaleaks/GLBackend/issues/18
    """
    specification = {}

