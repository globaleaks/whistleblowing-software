# -*- coding: UTF-8
#   Answers
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   This file contain the definition of all the answer struct perfomed by GLB,
#   and are used to make output validation, sanitization, and operations

# All the responses are organized in three keyword:
# First: destination domain (public, admin, wb = whistleblower, receiver, actors = wb + receiver in a tip)
# Second: element described (Receiver, Context, Tip, Node)
# Third: data type (Desc, is a dictionary, or a List, the struct represented can be present 0 to N-th times)
#
# This schema need to be documented in globaleaks/messages/README.md -- TODO

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
