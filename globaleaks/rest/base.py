# -*- coding: UTF-8
#
#   rest/base
#   *********
#
#   Contains all the logic handle input and output validation.

import inspect
import json
from datetime import datetime
from globaleaks.rest.errors import InvalidInputFormat


# XXX not true anymore, need to be update the specification and the glossary
fileGUS = r"(f_(\w){30,30})"
receiptGUS = r"(\d{10,10})"
submissionGUS = r"(s_(\w){50,50})"
receiverGUS = r"(r_(\w){20,20})"
contextGUS = r"(c_(\w){20,20})"
tipGUS = r"(t_(\w){50,50})"

uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'

# TODO: define this stuff
dateType = r'(.*)'
timeType = r'(.*)'

fileDict = {
            "name": unicode,
            "description": unicode,
            "size": int,
            "content_type": unicode,
            "date": dateType,
}

formFieldsDict = {
            "presentation_order": int,
            "label": unicode,
            "name": unicode,
            "required": bool,
            "hint": unicode,
            "type": unicode
}

