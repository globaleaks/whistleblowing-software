from globaleaks.utils import recurringtypes as GLT

"""
follow the internal filling methods called by the dummy filled below
"""

def __publicStatisticsDict(datao):

    datao.active_contexts = 2
    datao.active_receivers = 3
    datao.uptime_days = 100


def __nodePropertiesDict(datao):

    datao.AnonymousSubmissionOnly = True


def __fileDict(datao):

    datao.filename = "passwd.txt"
    datao.file_description = "a list of encrypted password"
    datao.size = "4242"
    datao.content_type = "plain/text"
    # datao.date
    datao.cleaned_meta_data = False


def __receiverDescriptionDict_0(datao):

    datao.rID = "r_ZEROrrAAAABBBBBBBBBBDDDDDDDDDDRRRRRRRRRRPPPPPPPPPP"
    datao.CanDeleteSubmission = True
    datao.CanPostponeExpiration = True
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = True
    datao.CanTriggerEscalation = True

    datao.receiver_name = "cool antivelox organization"
    datao.receiver_description = "we're fighting against wrong penalities since 1492"

    # one language is the default
    datao.LanguageSupported[0] = "IT"
    datao.LanguageSupported.append("string")
    datao.LanguageSupported[1] = "ES"


def __receiverDescriptionDict_1(datao):

    datao.rID = "r_ONErrAAAAABBBBBBBBBBDDDDDDDDDDRRRRRRRRRRPPPPPPPPPP"
    datao.CanDeleteSubmission = True
    datao.CanPostponeExpiration = True
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = True
    datao.CanTriggerEscalation = True

    datao.receiver_name = "the police chief"
    datao.receiver_description = "we're the police chief, we're the law"

    # one language is the default
    datao.LanguageSupported[0] = "ES"
    datao.LanguageSupported.append("string")
    datao.LanguageSupported[1] = "FR"


def __receiverDescriptionDict_2(datao):

    datao.rID = "r_TWOrrAAAAABBBBBBBBBBDDDDDDDDDDRRRRRRRRRRPPPPPPPPPP"
    datao.CanDeleteSubmission = False
    datao.CanPostponeExpiration = False
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = False
    datao.CanTriggerEscalation = False

    datao.receiver_name = "the police thug"
    datao.receiver_description = "we can close our eyes if an autovelox is reported to be wrong"

    datao.LanguageSupported[0] = "EN"
    datao.LanguageSupported.append("string")
    datao.LanguageSupported[1] = "KK"


def __receiverDescriptionDict_3(datao):

    datao.rID = "r_THREErrAAABBBBBBBBBBDDDDDDDDDDRRRRRRRRRRPPPPPPPPPP"
    datao.CanDeleteSubmission = False
    datao.CanPostponeExpiration = False
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = False
    datao.CanTriggerEscalation = False

    datao.receiver_name = "the guys with painting rifle"
    datao.receiver_description = "we can close the eyes of the autovelox"

    datao.LanguageSupported[0] = "IT"
    datao.LanguageSupported.append("string")
    datao.LanguageSupported[1] = "KK"


def __adminStatisticsDict(datao):

    datao.hours_interval = 3
    datao.download_number = 30
    datao.receiver_accesses = 40
    datao.submission_received = 2


def __formFieldsDict_0(datao):

    datao.presentation_order = 1
    datao.name = "city"
    datao.required = True
    datao.field_description = "the city of the autovelox"
    datao.field_type = "text"
    datao.value = "this is the default value"


def __formFieldsDict_1(datao):

    datao.presentation_order = 2
    datao.name = "road"
    datao.required = True
    datao.field_description = "the road where the autovelox is running"
    datao.field_type = "text"
    datao.value = "this is the default value"


def __formFieldsDict_2(datao):

    datao.presentation_order = 3
    datao.name = "penality details"
    datao.required = True
    datao.field_description = "put the number of the penality"
    datao.field_type = "int"
    datao.value = "this is the default value"


def __formFieldsDict_3(datao):

    datao.presentation_order = 4
    datao.name = "how do you know that ?"
    datao.required = False
    datao.field_description = "details: eg, do you present your case to a judge ?"
    datao.field_type = "text"
    datao.value = "this is the default value"


def __moduleDataDict_N(datao):

    datao.mID = "m_1234567890"
    datao.active = True
    datao.module_type = "notification"
    datao.name = "Encrypted E-Mail"
    datao.module_description = "with this module you can setup your own GPG key and receive safely the notice of a new tip, and your secret link"

    # --------------------------------------------------------------
    # datao.service_message = "Invalid Public Key provided"
    # datao.service_message = "Your PGP key is correctly configured"
    datao.service_message = "You have not yet configured your PGP key"
    # those was the first three "service_message" that come in mind,
    # this field act as report/error/status message from the module to 
    # the users.
    # this message is not displayed to the administrator

    __formFieldsDict_0(datao.admin_options[0])
    __formFieldsDict_1(datao.user_options[0])


def __moduleDataDict_D(datao):

    datao.mID = "m_0987654321"
    datao.active = True
    datao.module_type = "delivery"
    datao.name = "upload in FTP"
    datao.module_description = "with this module, you can found the data in your personal FTP"

    datao.service_message = "The latest time a delivery has been sent, it worked!"

    __formFieldsDict_0(datao.admin_options[0])
    __formFieldsDict_1(datao.user_options[0])


"""
remind: are declared FOUR fields by base
"""
def __contextDescriptionDict_0(datao):

    datao.cID = "c_AAAAAAAAAABBBBBBBBBBDcontextzeroRRRRRRRRPPPPPPPPPP"
    datao.name ="Autovelox broken"
    datao.context_description = "tell us which autovelox is working bad, we're tired of wrong fines!"
    # "creation_date", "time"
    # "append_date", "time"

    # only 1 form is *required*, other can be expanded
    __formFieldsDict_0(datao.fields[0])

    # datao.fields.append ( GLT.formFieldsDict() )
    # __formFieldsDict_1(datao.fields[1])
    # datao.fields.append ( GLT.formFieldsDict() )
    # __formFieldsDict_2(datao.fields[2])
    # datao.fields.append ( GLT.formFieldsDict() )
    # __formFieldsDict_3(datao.fields[3])

    datao.SelectableReceiver = False

    datao.receivers.append ( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_0(datao.receivers[0])
    #datao.receivers.append ( GLT.receiverDescriptionDict() )
    #__receiverDescriptionDict_1(datao.receivers[1])
    #datao.receivers.append ( GLT.receiverDescriptionDict() )
    #__receiverDescriptionDict_2(datao.receivers[2])
    #datao.receivers.append ( GLT.receiverDescriptionDict() )
    #__receiverDescriptionDict_3(datao.receivers[3])

    datao.EscalationTreshold = 4

    # this would be derived by the mix of the supported 
    # language in the receivers corpus
    datao.LanguageSupported.append( "string ")
    datao.LanguageSupported[0] = "EN"


def __contextDescriptionDict_1(datao):
    __contextDescriptionDict_0(datao)


def __commentDescriptionDict(datao):

    datao.writtentext = "Hello, I've readed your stuff, I like it"
    datao.commenttype = "receiver"
    datao.author = "Julian Hussein Manning"
    # date ? default


def __tipIndexDict(datao):

    datao.cID = "c_AAAAAAAAAABBcontextrandomDDDDDRRRRRRRRRRPPPPPPPPPP"

    datao.tiplist.append( GLT.tipSubIndex() )
    __tipSubIndex(datao.tiplist[0])


def __tipSubIndex(datao):

    datao.tID = "t_AAAAAAAAAATIPTIPTIPTIPTIPTIPxxRRRRRRRRRRKKKKKKKKKK"
    datao.tip_title = "Greatest secret of all world - Enter the ninja"

    datao.notification_adopted = "default email"
    datao.delivery_adopted = "default download"

    datao.download_limit = 5
    datao.download_performed = 2
    datao.access_limit = 100
    datao.access_performed = 33

    # default "expiration_date"
    # idem "creation_date"
    # idem "last_append_date"

    datao.comment_number = 4
    datao.folder_number = 2
    datao.overall_pertinence = 101


def tipDetailsDict(datao):

    __tipSubIndex(datao.tip)

    datao.tip_data.append( GLT.formFieldsDict() )
    __formFieldsDict_3(datao.tip_data[0])

    datao.folder.append( GLT.fileDict() )
    __fileDict(datao.folder[0])

    datao.comment.append( GLT.commentDescriptionDict() )
    __commentDescriptionDict(datao.comment[0])

    datao.receiver_selected.append( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_0(datao.receiver_selected)


def __localizationDict(datao):
    pass


"""
Those functions may be called by the various handlers, 
in example dummynode is called by node.py
"""
def NODE_ROOT_GET(datao):

    datao.contexts.append( GLT.contextDescriptionDict() )
    __contextDescriptionDict_0(datao.contexts[0])

    #datao.contexts.append( GLT.contextDescriptionDict() )
    #__contextDescriptionDict_1(datao.contexts[1])

    __publicStatisticsDict(datao.public_statistics)
    __nodePropertiesDict(datao.node_properties)

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
    __receiverDescriptionDict_1(datao.receivers_selected[0])

    datao.receivers_selected.append( GLT.receiverDescriptionDict() ) 
    __receiverDescriptionDict_2(datao.receivers_selected[1])

    # the first one is always present, because may not exists a submission
    # without almost 1 field
    __formFieldsDict_0(datao.fields[0])

    datao.fields.append( GLT.formFieldDict() )
    __formFieldsDict_1(datao.fields[1])

    datao.fields.append( GLT.formFieldDict() )
    __formFieldsDict_2(datao.fields[2])

def SUBMISSION_FILES_GET(datao):

    __fileDict(datao)

def RECEIVER_ROOT_GET(datao):

    __tipIndexDict(datao.tips)
    __receiverDescriptionDict_3(datao.receiver_properties)

    # both of them are already present, because do not exist
    # a backend with almost one of them.
    __moduleDataDict_N(datao.notification_method[0])
    __moduleDataDict_D(datao.delivery_method[0])

def RECEIVER_MODULE_GET(datao):

    # no one may be available
    datao.modules.append( GLT.moduleDataDict() )
    __moduleDataDict_N(datao.modules[0])

    datao.modules.append( GLT.moduleDataDict() )
    __moduleDataDict_D(datao.modules[1])

def TIP_ROOT_GET(datao):

    __tipDetailsDict(datao)

def ADMIN_NODE_GET(datao):

    datao.name = "don't track us: AUTOVELOX"

    __adminStatisticsDict(datao.admin_statistics)
    __publicStatisticsDict(datao.public_statistics)
    __nodePropertiesDict(datao.node_properties)

    datao.contexts.append( GLT.contextDescriptionDict() )
    __contextDescriptionDict_0(datao.contexts[0])

    datao.contexts.append( GLT.contextDescriptionDict() )
    __contextDescriptionDict_1(datao.contexts[1])

    datao.public_site = "http://www.matrixenter.int"
    datao.hidden_service = "cnwoecowiecnirnio23rn23io.onion"
    datao.url_schema = "/"


def ADMIN_CONTEXTS_GET(datao):

    datao.contexts.append( GLT.contextDescriptionDict() )
    __contextDescriptionDict_0(datao.contexts[0])


def ADMIN_RECEIVERS_GET(datao):

    datao.receivers.append( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_0(datao.receivers[0])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_1(datao.receivers[1])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_2(datao.receivers[2])
    datao.receivers.append( GLT.receiverDescriptionDict() )
    __receiverDescriptionDict_3(datao.receivers[3])

def ADMIN_MODULES_GET(datao):

    datao.modules.append( GLT.moduleDataDict() )
    __moduleDataDict_N(datao.modules[0])

    datao.modules.append( GLT.moduleDataDict() )
    __moduleDataDict_D(datao.modules[1])

