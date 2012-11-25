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
"""
Here should go the functions for generating the responses to be sent by a
GLBackend to a GLClient.

XXX
Initially we were thinking of doing sanitization of data in input and in ouput,
but I believe that since the client must be hostproof in the sense that if it
is purely client side loaded it should be responsible for sanitizing and
validating the messages that come in. For this reason I believe we should only
put here helper functions that are useful for generating complex responses, but
we should not worry about making sure the types of them are valid since we
already do validation on the input side.
"""

# This is the struct containing the errors
def errorMessage(http_error_code=500, error_dict={}):
    """
    errorMessage may be used as inline object declaration and assignment
    """
    response = {'http_error_code':  http_error_code,
                'error_code': error_dict.get('code'),
                'error_message': error_dict.get('string')}
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
                "contexts": null # contextDescriptionDict
                }
    # XXX run function to do validation of this data in output
    #
    #validateNodeMainSettings(response)

    # self.define("description", localization)
    # GlClient -- how would be handled the localization ?

    return response

# U2
def newSubmission(submission_gus, time):
    response = {
        "submission_gus": submission_gus,
        "creation_time": time
    }
    return response

# R1
def commonReceiverAnswer():
    response = {"tips": dummy.base.tipIndexDict,
            "receiver_properties": dummy.base.receiverDescriptionDicts,
            "notification_method": dummy.base.moduleDataDict_N,
            "delivery_method": dummy.base.moduleDataDict_D
    }
    return response

