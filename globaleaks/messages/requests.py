# -*- coding: UTF-8
#   Requests
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE

"""
This file contain the specification of all the requests that can be made by a
GLClient to a GLBackend.
These specifications may be used with messages.validateMessage() inside of the
handler to verify if the request is correct.
"""

from globaleaks.messages.base import GLTypes
from globaleaks.messages import base

class submissionStatus(GLTypes):
    """
    U3 (POST)
    """
    specification = {"fields": [base.formFieldsDict],
                     "context_selected": base.contextGUS}


class finalizeSubmission(GLTypes):
    """
    U4 (POST)
    """
    specification = {"proposed_receipt": unicode,
            "folder_name": unicode,
            "folder_description": unicode}

# U5 (file, CURD) -- not yet defined


class tipOperations(GLTypes):
    """
    T1 (POST) - receiver only
    """
    specification = {"personal_delete": bool,
            "submission_delete": bool,
            "escalate": bool}


class sendComment(GLTypes):
    """
    T2 (POST)
    """
    # this is wrong, comment is expected just as text, and is returned
    # with a commentDescriptionDict (inside there are some information that
    # are gurantee by server, not written by client)
    specification = {"comment": base.commentDescriptionDict}

# T3 (files) -- not yet defined


class finalizeIntegration(GLTypes):
    """
    T4 (POST - finalize Folder upload)
    """
    specification = {"folder_name": unicode,
            "folder_description": unicode}


class pertinenceVote(GLTypes):
    """
    T6 (POST) - receiver only
    """
    specification = {"pertinence": int}


class receiverOptions(GLTypes):
    """
    R2 (CURD)
    """
    specification = {"module": base.moduleDataDict}


class nodeAdminSetup(GLTypes):
    """
    A1 (POST)
    """
    specification = {"name": unicode,
            "admin_statistics_ratio": int,
            "public_statistics_ratio": int,
            "node_properties": base.nodePropertiesDict,

            "node_description": unicode,
            # GLT.localizationDict() )
            # XXX may exists different description fields, like "about us"
            # "privacy policy" and the other in the footer
            # also logo upload need to be handled

            "public_site": unicode,
            "hidden_service": unicode,
            "url_schema": unicode,

            "do_leakdirectory_update": bool,
            "new_admin_password": unicode
    }


class contextConfiguration(GLTypes):
    """
    A2 (CURD)
    """
    specification = {"context": base.contextDescriptionDict}


class receiverConfiguration(GLTypes):
    """
    A3 (CURD)
    """
    specification = {"receiver": base.receiverDescriptionDict}


class moduleConfiguration(GLTypes):
    """
    A4 (POST)
    """
    specification = {"module": base.moduleDataDict}


