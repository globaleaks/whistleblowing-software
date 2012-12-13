# -*- coding: UTF-8
#   Answers
#   *******
# 
#   This file contain the definition of all the answer struct perfomed by GLB,
#   and are used to make output validation, sanitization, and operations

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
