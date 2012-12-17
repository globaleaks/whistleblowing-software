# -*- coding: UTF-8
#
#   Answers
#   *******
# 
#   This file contain the definition of all the answer struct performed by GLB,
#   and are used to make output validation, sanitization, and operations


from globaleaks.rest.base import GLTypes, formFieldsDict, timeType

# All the REST interface SHARE the same structures between response and request
# and the generate_docs.py script check in responses.py and requests.py
# To avoid code duplication, here follow the classes duplicated.
# responses.py copy from requests.py:

from globaleaks.rest.requests import wbSubmissionDesc
from globaleaks.rest.requests import receiverProfileDesc
from globaleaks.rest.requests import receiverReceiverDesc
from globaleaks.rest.requests import receiverTipDesc
from globaleaks.rest.requests import actorsCommentDesc
from globaleaks.rest.requests import adminContextDesc
from globaleaks.rest.requests import adminReceiverDesc
from globaleaks.rest.requests import adminPluginDesc
from globaleaks.rest.requests import adminProfileDesc


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
        'leakdirectory_entry': unicode,
        'public_stats_delta' : int
    }

class publicContextDesc(GLTypes):

    specification =  {
        'name': unicode,
        'description' : unicode,
        'fields' : [ formFieldsDict ],
        'selectable_receiver': bool,
        'languages_supported': unicode,
        'tip_timetolive' : int,
        'creation_date' : timeType,
        'update_date' : timeType
    }

class publicReceiverDesc(GLTypes):

    specification =  {
        'name' : unicode,
        'description' : unicode,
        'tags' : unicode,
        'know_languages' : unicode
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

class receiverProfileList(GLTypes):

    specification = [ receiverProfileDesc ]

class receiverTipList(GLTypes):

    specification = [ receiverTipDesc ]

class actorsCommentList(GLTypes):

    specification = [ actorsCommentDesc ]

class actorsReceiverList(GLTypes):

    specification = [ receiverReceiverDesc ]

class adminReceiverList(GLTypes):

    specification = [ adminReceiverDesc ]

class adminContextList(GLTypes):

    specification =  [ adminContextDesc ]

class adminPluginList(GLTypes):

    specification = [ adminPluginDesc ]

class adminProfileList(GLTypes):

    specification = [ adminProfileDesc ]


