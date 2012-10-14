# -*- encoding: utf-8 -*-
#
# :authors: Claudio Agosti, Arturo Filastò
# :licence: see LICENSE

from globaleaks.messages.dummy import base

"""
Those functions may be called by the various handlers,
in example NODE_ROOT_GET is called by node.py
"""
nodeRootGet = {"contexts": [base.contextDescriptionDicts[0]],
    "public_statistics": base.publicStatisticsDict,
    "node_properties": base.nodePropertiesDict,
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
    "receivers_selected": [base.receiverDescriptionDicts[0],
                           base.receiverDescriptionDicts[1]],

    "fields": [base.formFieldsDicts[0],
               base.formFieldsDicts[1],
               base.formFieldsDicts[2]]
}


submissionFilesGet = base.fileDicts[0].copy()

receiverRootGet = {
    "tips": base.tipIndexDict,
    "receiver_properties": base.receiverDescriptionDicts[3],

    # both of them are already present, because do not exist
    # a backend with almost one of them.

    "notification_method": [base.moduleDataDict_N],
    "delivery_method": [base.moduleDataDict_D]
}

receiverModuleGet = {
    # no one may be available
    "modules": [base.moduleDataDict_N, base.moduleDataDict_D]
}

tipRootGet = base.tipDetailsDict.copy()

adminNodeGet = {
    "name":  "don't track us: AUTOVELOX",

    "admin_statistics": base.adminStatisticsDict,
    "public_statistics": base.publicStatisticsDict,
    "node_properties": base.nodePropertiesDict,

    "contexts": [base.contextDescriptionDicts[0],
                 base.contextDescriptionDicts[1]],

    "public_site":  "http://www.matrixenter.int",
    "hidden_service":  "cnwoecowiecnirnio23rn23io.onion",
    "url_schema":  "/"
}

adminContextsGet = {
    "contexts": [base.contextDescriptionDicts[0]]
}

adminReceiversGet = {
    "receivers": base.receiverDescriptionDicts
}

adminModulesGet = {
    "modules": [base.moduleDataDict_N,
                base.moduleDataDict_D]
}

