# -*- encoding: utf-8 -*-
#
# :authors: Claudio Agosti, Arturo Filastò
# :licence: see LICENSE

from globaleaks.utils import idops
from globaleaks.messages.dummy import shared

submissionStatusPost = {"receiver_selected": idops.random_receiver_id(),
    "fields": [shared.formFieldsDicts[0]]
}

submissionSubmitPost = {"receiver_selected": idops.random_receiver_id(),
    "fields": [shared.formFieldsDicts[0]]
}

submissionFinalizePost = {"proposed_receipt": "this is my secret receipt",
    "folder_name":  "MY first file pack",
    "folder_description":  "This stuff rox, I've collected for years"
}


# T1 tipOperations
tipOptionsPost = {
    "personal_delete":  False,
    "submission_delete":  False,
    "escalate":  True
}


# T2 sendComment
tipOptionsPost = {
    "comment": shared.commentDescriptionDict
}

# T3 (files) -- not yet defined


# T4 finalizeIntegration
tipFinalizePost = {
    "folder_name":  "another roxxing block of files",
    "folder_description":  "the 1st is from JIM, the 2nd from MIJ"
}


# T6 pertinenceVote
tipPertinencePost = {
    "pertinence":  102
}

# R2 receiverOptions
receiverModulePost = {
    # optional: POST hack
    "module": shared.moduleDataDict_N
}

# R2 receiverOptions
receiverModulePut = {
    "module": shared.moduleDataDict_N
}


# R2 receiverOptions
receiverModuleDelete = {
    "module": shared.moduleDataDict_N
}

# A1 nodeAdminSetup
adminNodePost = {
    "name":  "new name for the node",
    "admin_statistics_ratio":  2,
    "public_statistics_ratio":  3,
    "node_properties": shared.nodePropertiesDict,

    "node_description":  "well, I'm a node, you know ?",
    "public_site":  "https://asimpleleaksite.blogspot.come",
    "hidden_service":  "3jr2fnowefnioewnfewnfklw.onion",
    "url_schema":   "/",

    "do_leakdirectory_update":  True,
    "new_admin_password":  ""
}


# A2 contextConfiguration
adminContextsPost = {
    "context": shared.contextDescriptionDicts[0]
}

# A2 contextConfiguration
adminContextsPut = {
    "context": shared.contextDescriptionDicts[0]
}

# A2 contextConfiguration
adminContextsDelete = {
    "context": shared.contextDescriptionDicts[0]
}


# A3 receiverConfiguration
adminReceiversPost = {
    # optional: POST hack
    "receivers": shared.receiverDescriptionDicts[0]
}

# A3 receiverConfiguration
adminReceiversPut = {
    "receivers": shared.receiverDescriptionDicts[0]
}


# A3 receiverConfiguration
adminReceiversDelete = {
    "receivers": shared.receiverDescriptionDicts[0]
}


# A4 moduleConfiguration
adminModulesPost = {
    "module": shared.moduleDataDict_N
}


