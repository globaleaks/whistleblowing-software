from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import idops
from globaleaks.utils.dummy import dummy_shared as shared

"""
Those functions may be called by the various handlers, 
in example NODE_ROOT_GET is called by node.py
"""
def NODE_ROOT_GET(datao):

    datao.contexts.append( GLT.contextDescriptionDict() )
    shared._contextDescriptionDict0(datao.contexts[0])

    #datao.contexts.append( GLT.contextDescriptionDict() )
    #_contextDescriptionDict1(datao.contexts[1])

    shared._publicStatisticsDict(datao.public_statistics)
    shared._nodePropertiesDict(datao.node_properties)

    datao.public_site = "http://www.matrixenter.int"
    datao.hidden_service = "cnwoecowiecnirnio23rn23io.onion"
    datao.url_schema = "/"
    datao.name = "don't track us: AUTOVELOX"

def SUBMISSION_NEW_GET(datao):

    # this would be useless when the default value would
    # be already assigned
    datao.submission_id = "s_AAAAAAAAAABBBBBBBBBBDDDDDDsubmissionRRRRPPPPPPPPPP"

def SUBMISSION_STATUS_GET(datao):

    datao.receivers_selected.append( GLT.receiverDescriptionDict() ) 
    shared._receiverDescriptionDict1(datao.receivers_selected[0])

    datao.receivers_selected.append( GLT.receiverDescriptionDict() ) 
    shared._receiverDescriptionDict2(datao.receivers_selected[1])

    # the first one is always present, because may not exists a submission
    # without almost 1 field
    shared._formFieldsDict0(datao.fields[0])

    datao.fields.append( GLT.formFieldDict() )
    shared._formFieldsDict1(datao.fields[1])

    datao.fields.append( GLT.formFieldDict() )
    shared._formFieldsDict2(datao.fields[2])

def SUBMISSION_FILES_GET(datao):

    shared._fileDict(datao)

def RECEIVER_ROOT_GET(datao):

    shared._tipIndexDict(datao.tips)
    shared._receiverDescriptionDict3(datao.receiver_properties)

    # both of them are already present, because do not exist
    # a backend with almost one of them.
    shared._moduleDataDict_N(datao.notification_method[0])
    shared._moduleDataDict_D(datao.delivery_method[0])

def RECEIVER_MODULE_GET(datao):

    # no one may be available
    datao.modules.append( GLT.moduleDataDict() )
    shared._moduleDataDict_N(datao.modules[0])

    datao.modules.append( GLT.moduleDataDict() )
    shared._moduleDataDict_D(datao.modules[1])

def TIP_ROOT_GET(datao):

    shared._tipDetailsDict(datao)

def ADMIN_NODE_GET(datao):

    datao.name = "don't track us: AUTOVELOX"

    shared._adminStatisticsDict(datao.admin_statistics)
    shared._publicStatisticsDict(datao.public_statistics)
    shared._nodePropertiesDict(datao.node_properties)

    datao.contexts.append( GLT.contextDescriptionDict() )
    shared._contextDescriptionDict0(datao.contexts[0])

    datao.contexts.append( GLT.contextDescriptionDict() )
    shared._contextDescriptionDict1(datao.contexts[1])

    datao.public_site = "http://www.matrixenter.int"
    datao.hidden_service = "cnwoecowiecnirnio23rn23io.onion"
    datao.url_schema = "/"


def ADMIN_CONTEXTS_GET(datao):

    datao.contexts.append( GLT.contextDescriptionDict() )
    shared._contextDescriptionDict0(datao.contexts[0])


def ADMIN_RECEIVERS_GET(datao):

    datao.receivers.append( GLT.receiverDescriptionDict() )
    shared._receiverDescriptionDict0(datao.receivers[0])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    shared._receiverDescriptionDict1(datao.receivers[1])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    shared._receiverDescriptionDict2(datao.receivers[2])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    shared._receiverDescriptionDict3(datao.receivers[3])

def ADMIN_MODULES_GET(datao):

    datao.modules.append( GLT.moduleDataDict() )
    shared._moduleDataDict_N(datao.modules[0])

    datao.modules.append( GLT.moduleDataDict() )
    shared._moduleDataDict_D(datao.modules[1])

