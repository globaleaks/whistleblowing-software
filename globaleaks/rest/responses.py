# -*- coding: UTF-8
#
#   Answers
#   *******
# 
#   This file contain the definition of all the answer struct performed by GLB,
#   and are used to make output validation, sanitization, and operations


from globaleaks.rest.base import GLTypes, formFieldsDict, timeType, receiverGUS, contextGUS, profileGUS

# All the REST interface SHARE the same structures between response and request
# and the generate_docs.py script check in responses.py and requests.py
# To avoid code duplication, here follow the classes duplicated.
# responses.py copy from requests.py:

from globaleaks.rest.requests import receiverReceiverDesc
from globaleaks.rest.requests import receiverTipDesc
from globaleaks.rest.requests import actorsCommentDesc
from globaleaks.rest.requests import adminContextDesc
from globaleaks.rest.requests import adminReceiverDesc
from globaleaks.rest.requests import adminProfileDesc
from globaleaks.rest.requests import receiverConfDesc


# -------------------------------------------------------
# Here start the definition of the Response-only messages

class adminStatsDesc(GLTypes):
    """
    Admin Stats, information useful to the admin, for understand
    They need to be implemented and specified, too :((
    """

    specification = {
        'started_submission' : int,
        'completed_submission' : int,
        'receiver_accesses' : int,
        'wb_accesses' : int,
        'refused_receiver_auth' : int,
        'refused_wb_auth' : int,
        'comments' : int
    }

class publicNodeDesc(GLTypes):

    specification = {
        'name': unicode,
        'description' : unicode,
        'hidden_service' : unicode,
        'public_site' : unicode,
        'public_stats_update_time' : int,
        'email' : unicode,
        'languages' : list
    }

class publicContextDesc(GLTypes):

    specification =  {
        'name': unicode,
        'description' : unicode,
        'fields' : [ formFieldsDict ],
        'selectable_receiver': bool,
        'languages': list,
        'tip_timetolive' : int,
        'creation_date' : timeType,
        'update_date' : timeType
    }

class publicReceiverDesc(GLTypes):

    specification =  {
        'name' : unicode,
        'description' : unicode,
        'tags' : unicode,
        'languages' : unicode
    }

class publicReceiverList(GLTypes):

    specification = [ publicReceiverDesc ]

class publicContextList(GLTypes):

    specification = [ publicContextDesc ]

class publicStatsDesc(GLTypes):
    """
    Public statistic, just information that would be useful to the
    public, to make well know if a GL Node has live inside or dead.

    tip_accesses is the sum of wb_accesses and receiver_accesses
    from the adminStatsElement
    """
    specification = {
        'completed_submission' : int,
        'tip_accesses' : int
    }

class publicStatsList(GLTypes):

    specification = [ publicStatsDesc ]

class adminStatsList(GLTypes):

    specification = [ adminStatsDesc ]

class receiverTipList(GLTypes):

    specification = [ receiverTipDesc ]

class actorsTipDesc(GLTypes):

    specification =  {
        'fields' : dict,
        'pertinence_counter' : int,
        'escalation_threshold' : int,
        'creation_date' : timeType,
        'expiration_date' : timeType,
        'last_activity' : timeType,
        'access_limit' : int,
        'download_limit' : int
    }

class actorsCommentList(GLTypes):

    specification = [ actorsCommentDesc ]

class actorsReceiverList(GLTypes):

    specification = [ receiverReceiverDesc ]

class adminReceiverList(GLTypes):

    specification = [ adminReceiverDesc ]

class adminContextList(GLTypes):

    specification =  [ adminContextDesc ]

class receiverProfileDesc(GLTypes):

    specification = {
        'receiver_gus' : receiverGUS,
        'context_gus' : contextGUS,
        'receiver_fields' : [ formFieldsDict ],
        'profile_gus' : profileGUS,
        'plugin_name' : unicode,
        'profile_description': unicode
    }

class receiverProfileList(GLTypes):

    specification = [ receiverProfileDesc ]

class receiverConfList(GLTypes):

    specification = [ receiverConfDesc ]

class adminPluginDesc(GLTypes):

    specification = {
        'plugin_name' : unicode,
        'plugin_type' : unicode,
        'plugin_description' : unicode,
        'admin_fields' : [ formFieldsDict ],
        'receiver_fields' : [ formFieldsDict ]
    }

class adminPluginList(GLTypes):

    specification = [ adminPluginDesc ]

class adminProfileList(GLTypes):

    specification = [ adminProfileDesc ]


