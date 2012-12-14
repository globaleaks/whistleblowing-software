# -*- coding: UTF-8
#
#   Answers
#   *******
# 
#   This file contain the definition of all the answer struct performed by GLB,
#   and are used to make output validation, sanitization, and operations


from globaleaks.rest.base import GLTypes

class publicStatsElement(GLTypes):
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

    specification = {
        'public_stats' : [ publicStatsElement ]
    }

class adminStatsElement(GLTypes):
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

class adminStatsList(GLTypes):

    specification = {
        'admin_stats' : [ adminStatsElement ]
    }













# All the REST interface SHARE the same structures between response and request
# and the generate_docs.py script check in responses.py and requests.py
# To avoid code duplication, here follow the classes duplicated.
# responses.py copy from requests.py:

from globaleaks.rest.requests import wbSubmissionDesc as imported_wbSubmissionDesc
wbSubmissionDesc = imported_wbSubmissionDesc


































"""
adminNodeDesc

        The two "_delta" variables, mean the minutes interval for collect statistics,
        because the stats are collection of the node status made over periodic time,

    'name': 'string',
    'admin_statistics': '$adminStatisticsDict',
    'public_stats': '$publicStatisticsDict,
    'node_properties': '$nodePropertiesDict',
    'contexts': [ '$contextDescriptionDict', { }, ],
    'node_description': '$localizationDict',
    'public_site': 'string',
    'hidden_service': 'string',
    'url_schema': 'string'


adminContextDesc
   {
    "context_gus": "context_gus"
    "name": "string"
    "context_description": "string"
    "creation_date": "time"
    "update_date": "time"
    "fields": [ formFieldsDict ]
    "SelectableReceiver": "bool"
    "receivers": [ receiverDescriptionDict ]
    "escalation_threshold": "int"
    "LanguageSupported": [ "string" ]
   }

adminContextList

publicContextDesc
   {
    "context_gus": "context_gus"
    "name": "string"
    "context_description": "string"
    "creation_date": "time"
    "update_date": "time"
    "fields": [ formFieldsDict ]
    "SelectableReceiver": "bool"
    "receivers": [ receiverDescriptionDict ]
    "escalation_threshold": "int"
    "LanguageSupported": [ "string" ]
   }

adminReceiverList


publicReceiverDesc

adminReceiverDesc


adminPluginList


"""
