from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import idops
from globaleaks.utils.dummy import dummy_shared as shared


# U3 - submissionUpdate
def SUBMISSION_STATUS_POST(datao):

    datao.receiver_selected.append(idops.random_receiver_id() )
    # datao.receiver_selected[0] = idops.random_receiver_id()
    # without a meaningfull ID, allocation & assignment fits well

    datao.fields.append( GLT.formFieldsDict() )
    shared._formFieldsDict0(datao.fields[0])


# U4 finalizeSubmission
def SUBMISSION_FINALIZE_POST(datao):

    datao.proposed_receipt = "this is my secret receipt"
    datao.folder_name = "MY first file pack"
    datao.folder_description = "This stuff rox, I've collected for years"


# T1 tipOperations
def TIP_OPTIONS_POST(datao):

    datao.personal_delete = False
    datao.submission_delete = False
    datao.escalate = True


# T2 sendComment
def TIP_COMMENT_POST(datao):

    shared._commentDescriptionDict(datao.comment)


# T3 (files) -- not yet defined


# T4 finalizeIntegration
def TIP_FINALIZE_POST(datao):

    datao.folder_name = "another roxxing block of files"
    datao.folder_description = "the 1st is from JIM, the 2nd from MIJ"


# T6 pertinenceVote
def TIP_PERTINENCE_POST(datao):

    datao.pertinence = 102


# R2 receiverOptions
def RECEIVER_MODULE_POST(datao):

    # optional: POST hack
    shared._moduleDataDict_N(datao.module)


# R2 receiverOptions
def RECEIVER_MODULE_PUT(datao):

    shared._moduleDataDict_N(datao.module)


# R2 receiverOptions
def RECEIVER_MODULE_DELETE(datao):

    shared._moduleDataDict_N(datao.module)

# A1 nodeAdminSetup
def ADMIN_NODE_POST(datao):

    datao.name = "new name for the node"
    datao.admin_statistics_ratio = 2
    datao.public_statistics_ratio = 3 
    shared._nodePropertiesDict(datao.node_properties)

    datao.node_description = "well, I'm a node, you know ?"
    datao.public_site = "https://asimpleleaksite.blogspot.come"
    datao.hidden_service = "3jr2fnowefnioewnfewnfklw.onion"
    datao.url_schema =  "/"

    datao.do_leakdirectory_update = True
    datao.new_admin_password = ""


# A2 contextConfiguration
def ADMIN_CONTEXTS_POST(datao):

    # optional: POST hack
    shared._contextDescriptionDict0(datao.context)


# A2 contextConfiguration
def ADMIN_CONTEXTS_PUT(datao):

    shared._contextDescriptionDict0(datao.context)


# A2 contextConfiguration
def ADMIN_CONTEXTS_DELETE(datao):

    shared._contextDescriptionDict0(datao.context)


# A3 receiverConfiguration
def ADMIN_RECEIVERS_POST(datao):

    # optional: POST hack
    shared._receiverDescriptionDict0(datao.receiver)


# A3 receiverConfiguration
def ADMIN_RECEIVERS_PUT(datao):

    shared._receiverDescriptionDict0(datao.receiver)


# A3 receiverConfiguration
def ADMIN_RECEIVERS_DELETE(datao):

    shared._receiverDescriptionDict0(datao.receiver)


# A4 moduleConfiguration
def ADMIN_MODULES_POST(datao):

    shared._moduleDataDict_N(datao.module)



