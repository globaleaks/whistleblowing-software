# -*- coding: UTF-8
#
#   Answers
#   *******
#
#   This file contain the definition of all the answer struct performed by GLB,
#   and are used to make output validation, sanitization, and operations


# All the REST interface SHARE the same structures between response and request
# and the generate_docs.py script check in responses.py and requests.py
# To avoid code duplication, here follow the classes duplicated.
# responses.py copy from requests.py:

from globaleaks.rest.requests import receiverReceiverDesc
from globaleaks.rest.requests import receiverTipDesc
from globaleaks.rest.requests import actorsCommentDesc
from globaleaks.rest.requests import adminContextDesc
from globaleaks.rest.requests import adminReceiverDesc
from globaleaks.rest.base import *


# -------------------------------------------------------
# Here start the definition of the Response-only messages

adminStatsDesc = {
        'started_submission' : int,
        'completed_submission' : int,
        'receiver_accesses' : int,
        'wb_accesses' : int,
        'refused_receiver_auth' : int,
        'refused_wb_auth' : int,
        'comments' : int
    }

publicNodeDesc = {
        'name': unicode,
        'description' : unicode,
        'hidden_service' : unicode,
        'public_site' : unicode,
        'public_stats_update_time' : int,
        'email' : unicode,
        'languages' : list
    }

publicContextDesc =  {
        'name': unicode,
        'description' : unicode,
        'fields' : [ formFieldsDict ],
        'selectable_receiver': bool,
        'languages': list,
        'tip_timetolive' : int,
        'creation_date' : timeType,
        'update_date' : timeType
    }

publicReceiverDesc =  {
        'name' : unicode,
        'description' : unicode,
        'tags' : unicode,
        'languages' : unicode
    }

publicReceiverList = [ publicReceiverDesc ]

publicContextList = [ publicContextDesc ]

publicStatsDesc = {
        'completed_submission' : int,
        'tip_accesses' : int
    }

publicStatsList = [ publicStatsDesc ]

adminStatsList = [ adminStatsDesc ]

receiverTipList  = [ receiverTipDesc ]

actorsTipDesc =  {
        'fields' : dict,
        'pertinence_counter' : int,
        'escalation_threshold' : int,
        'creation_date' : timeType,
        'expiration_date' : timeType,
        'last_activity' : timeType,
        'access_limit' : int,
        'download_limit' : int
    }

actorsCommentList = [ actorsCommentDesc ]
actorsReceiverList = [ receiverReceiverDesc ]
adminReceiverList = [ adminReceiverDesc ]
adminContextList =  [ adminContextDesc ]
adminPluginDesc = {
        'plugin_name' : unicode,
        'plugin_type' : unicode,
        'plugin_description' : unicode,
        'admin_fields' : [ formFieldsDict ],
        'receiver_fields' : [ formFieldsDict ]
    }

adminPluginList = [ adminPluginDesc ]
