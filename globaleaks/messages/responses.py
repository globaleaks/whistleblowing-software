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

from globaleaks.messages import dummy

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
def nodeMainSettings():
    response = {"name": "myName",
                "public_site": "https://example.com/",
                "hidden_service": "http://foo.onion/",
                "url_schema": "https",
                "node_properties": {"anonymous_submission_only": True},
                "public_statistics": {'active_contexts': 1,
                                      'active_receivers': 10,
                                      'uptime_days': 100},
                "contexts": dummy.base.contextDescriptionDicts
                }
    # XXX run function to do validation of this data in output
    #
    #validateNodeMainSettings(response)

    # self.define("description", localization)
    # GlClient -- how would be handled the localization ?

    return response

# U2
def newSubmission():
    response = {
        "submission_id": submissionID,
        "creation_time": time
    }
    return response

# R1
class commonReceiverAnswer(GLT.GLTypes):
    response = {"tips": GLT.tipIndexDict,
            "receiver_properties": dummy.base.receiverDescriptionDicts,
            "notification_method": dummy.base.moduleDataDict,
            "delivery_method": dummy.base.moduleDataDict
    }
    return response

