# -*- encoding: utf-8 -*-
#
# :authors: Claudio Agosti, Arturo Filastò
# :licence: see LICENSE

from globaleaks.utils import idops
from globaleaks.messages.dummy import shared

"""
Those functions may be called by the various handlers,
in example NODE_ROOT_GET is called by node.py
"""
nodeRootGet = {"contexts": [shared.contextDescriptionDicts[0]],
    "public_statistics": shared.publicStatisticsDict,
    "node_properties": shared.nodePropertiesDict,
    "public_site":  "http://www.matrixenter.int",
    "hidden_service":  "cnwoecowiecnirnio23rn23io.onion",
    "url_schema":  "/",
    "name":  "don't track us: AUTOVELOX"
}

submissionNewGet = {
    # this would be useless when the default value would
    # be already assigned
    "submission_id":  "s_AAAAAAAAAABBBBBBBBBBDDDDDDsubmissionRRRRPPPPPPPPPP"
}

submissionStatusGet = {
    "receivers_selected": [shared.receiverDescriptionDicts[0],
                           shared.receiverDescriptionDicts[1]],

    "fields": [shared.formFieldsDicts[0],
               shared.formFieldsDicts[1],
               shared.formFieldsDicts[2]]
}


submissionFilesGet = shared.fileDicts[0].copy()

receiverRootGet = {
    "tips": shared.tipIndexDict,
    "receiver_properties": shared.receiverDescriptionDicts[3],

    # both of them are already present, because do not exist
    # a backend with almost one of them.

    "notification_method": [shared.moduleDataDict_N],
    "delivery_method": [shared.moduleDataDict_D]
}

receiverModuleGet = {
    # no one may be available
    "modules": [shared.moduleDataDict_N, shared.moduleDataDict_D]
}

tipRootGet = shared.tipDetailsDict.copy()

adminNodeGet = {
    "name":  "don't track us: AUTOVELOX",

    "admin_statistics": shared.adminStatisticsDict,
    "public_statistics": shared.publicStatisticsDict,
    "node_properties": shared.nodePropertiesDict,

    "contexts": [shared.contextDescriptionDicts[0],
                 shared.contextDescriptionDicts[1]],

    "public_site":  "http://www.matrixenter.int",
    "hidden_service":  "cnwoecowiecnirnio23rn23io.onion",
    "url_schema":  "/"
}

adminContextsGet = {
    "contexts": [shared.contextDescriptionDicts[0]]
}

adminReceiversGet = {
    "receivers": shared.receiverDescriptionDicts
}

adminModulesGet = {
    "modules": [shared.moduleDataDict_N,
                shared.moduleDataDict_D]
}

