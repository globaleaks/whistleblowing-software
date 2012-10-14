# -*- coding: UTF-8
#   Answers
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   This file contain the definition of all the answer struct perfomed by GLB
#   is used by curteg client (for verifiy that the answer fit with the expected format)
#   and by glbackend for format & sanitize output

from globaleaks.messages.dummy import answers

# This is the struct containing the errors
def errorMessage(httpErrorCode=500, errorDict={}):
    """
    errorMessage may be used as inline object declaration and assignment
    """
    response = {'http_error_code':  httpErrorCode,
                'error_code': errorDict.get('code'),
                'error_message': errorDict.get('string')}
    return response

# U1
def nodeRoot():
    response = answers.nodeRootGet.copy()
    # "description", localization)
    # GlClient -- how would be handled the localization ?
    return response

# U2
def newSubmission():
    response = { "submission_id": 'submissionID',
            "creation_time": 'time'}
    return response

# U3
def submissionStatus():
    response = answers.submissionStatusGet
    return response

# U4
def finalizeSubmission():
    response = {'receipt': 'receiptID'}
    return response

# U5 -- files -- TODO

# T1 use the base GLT.tipDetailsDict

# R1
def commonReceiverAnswer():
    response = answers.receiverRootGet
    return response

# R2
def receiverModuleAnswer():
    response = {"modules": [{"mID": "moduleID",
                            "active": True,
                            "module_type": 'notification',
                            "name": unicode('foobar'),
                            "module_description": unicode('foobar'),
                            "service_message": unicode('blabla'),
                            "admin_options": [{}],
                            "user_options": [{}]}
                            ]
    }
    return response


# A1
def nodeMainSettings():
    response = answers.adminNodeGet
    return response

# A2
def adminContextsCURD():
    response = answers.adminContextsGet
    return response

# A3
def adminReceiverCURD():
    response = answers.adminReceiversGet
    return response

# A4
def adminModulesUR():
    response = answers.adminModulesGet
    return response

