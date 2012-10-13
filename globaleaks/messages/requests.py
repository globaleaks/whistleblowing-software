# -*- coding: UTF-8
#   Requests
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   This file contain the definition of all the requests struct perfomed to GLB
#   is used by curteg client (for compose the requests) and by GLB (to sanitize having the
#   right structured code)

from globaleaks.messages.base import GLTypes
from globaleaks.messages import base

# U3 (POST)
class submissionStatus(GLTypes):
    specification = {"fields": [base.formFieldsDict],
                     "receiver_selected": [base.receiverID]}

# U4 (POST)
class finalizeSubmission(GLTypes):
    specification = {"proposed_receipt": unicode,
            "folder_name": unicode,
            "folder_description": unicode}

# U5 (file, CURD) -- not yet defined

# T1 (POST) - receiver only
class tipOperations(GLTypes):

    specification = {"personal_delete": bool,
            "submission_delete": bool,
            "escalate": bool}

# T2 (POST)
class sendComment(GLTypes):
    specification = {"comment": base.commentDescriptionDict}

# T3 (files) -- not yet defined

# T4 (POST - finalize Folder upload)
class finalizeIntegration(GLTypes):
    specification = {"folder_name": unicode,
            "folder_description": unicode}

# T6 (POST) - receiver only
class pertinenceVote(GLTypes):
    specification = {"pertinence": int}

# R2 (CURD)
class receiverOptions(GLTypes):
    specification = {"module": base.moduleDataDict}

# A1 (POST)
class nodeAdminSetup(GLTypes):

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

# A2 (CURD)
class contextConfiguration(GLTypes):
    specification = {"context": base.contextDescriptionDict}

# A3 (CURD)
class receiverConfiguration(GLTypes):
    specification = {"receiver": base.receiverDescriptionDict}

# A4 (POST)
class moduleConfiguration(GLTypes):
    specification = {"module": base.moduleDataDict}


