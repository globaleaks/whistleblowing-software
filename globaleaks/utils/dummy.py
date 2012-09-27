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
    pass

def __receiverDescriptionDict_0(datao):

    datao.rID = "r_HIGLEVEL_1_ID"
    datao.CanDeleteSubmission = True
    datao.CanPostponeExpiration = True
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = True
    datao.CanTriggerEscalation = True

    datao.receiver_name = "cool antivelox organization"
    datao.receiver_description = "we're fighting against wrong penalities since 1492"

    datao.LanguageSupported[0] = "IT"
    datao.LanguageSupported[1] = "PZ"

def __receiverDescriptionDict_1(datao):

    datao.rID = "r_HIGHLEVEL_2_ID"
    datao.CanDeleteSubmission = True
    datao.CanPostponeExpiration = True
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = True
    datao.CanTriggerEscalation = True

    datao.receiver_name = "the police chief"
    datao.receiver_description = "we're the police chief, we're the law"

    datao.LanguageSupported[0] = "ES"
    datao.LanguageSupported[1] = "PZ"

def __receiverDescriptionDict_2(datao):

    datao.rID = "r_LOWLEVEL_3_ID"
    datao.CanDeleteSubmission = False
    datao.CanPostponeExpiration = False
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = False
    datao.CanTriggerEscalation = False

    datao.receiver_name = "the police thug"
    datao.receiver_description = "we can close our eyes if an autovelox is reported to be wrong"

    datao.LanguageSupported[0] = "EN"
    datao.LanguageSupported[1] = "KK"

def __receiverDescriptionDict_3(datao):

    datao.rID = "r_LOWLEVEL_4_ID"
    datao.CanDeleteSubmission = False
    datao.CanPostponeExpiration = False
    datao.CanConfigureNotification = True
    datao.CanConfigureDelivery = False
    datao.CanTriggerEscalation = False

    datao.receiver_name = "the guys with painting rifle"
    datao.receiver_description = "we can close the eyes of the autovelox"

    datao.LanguageSupported[0] = "IT"
    datao.LanguageSupported[1] = "KK"


def __adminStatisticsDict(datao):
    pass

def __formFieldsDict_0(datao):

    datao.presentation_order = 1
    datao.name = "city"
    datao.required = True
    datao.field_description = "the city of the autovelox"
    datao.field_type = "text"

def __formFieldsDict_1(datao):

    datao.presentation_order = 2
    datao.name = "road"
    datao.required = True
    datao.field_description = "the road where the autovelox is running"
    datao.field_type = "text"

def __formFieldsDict_2(datao):

    datao.presentation_order = 3
    datao.name = "penality details"
    datao.required = True
    datao.field_description = "put the number of the penality"
    datao.field_type = "int"

def __formFieldsDict_3(datao):

    datao.presentation_order = 4
    datao.name = "how do you know that ?"
    datao.required = False
    datao.field_description = "details: eg, do you present your case to a judge ?"
    datao.field_type = "text"

def __moduleDataDict(datao):
    pass

"""
remind: are declared TWO contexts in the dummy
"""
def __contextDescriptionDict_0(datao):

    datao.cID = "c_CONTEXT_1"
    datao.name ="Autovelox broken"
    datao.context_description = "tell us which autovelox is working bad, we're tired of wrong fines!"
    # "creation_date", "time"
    # "update_date", "time"

    __formFieldsDict_0(datao.fields[0])
    __formFieldsDict_1(datao.fields[1])
    __formFieldsDict_2(datao.fields[2])
    __formFieldsDict_3(datao.fields[3])

    datao.SelectableReceiver = False

    __receiverDescriptionDict_0(datao.receivers[0])
    __receiverDescriptionDict_1(datao.receivers[1])
    __receiverDescriptionDict_2(datao.receivers[2])
    __receiverDescriptionDict_3(datao.receivers[3])

    datao.EscalationTreshold = 4

    # this would be derived by the mix of the supported 
    # language in the receivers corpus
    datao.LanguageSupported[0] = "EN"
    datao.LanguageSupported[1] = "IT"
    datao.LanguageSupported[2] = "PZ"
    datao.LanguageSupported[3] = "KK"
    datao.LanguageSupported[4] = "ES"

def __contextDescriptionDict_1(datao):
    __contextDescriptionDict_0(datao)


def __commentDescriptionDict(datao):
    pass

def __tipIndexDict(datao):
    pass

def __tipSubIndex(datao):
    pass

def __tipDetailsDict(datao):
    pass

def __localizationDict(datao):
    pass


"""
Those functions may be called by the various handlers, 
in example dummynode is called by node.py
"""

def NODE_ROOT_GET(datao):

    datao.define("contexts", GLT.contextDescriptionDict() )
    datao.extension("contexts", GLT.contextDescriptionDict() )

    __publicStatisticsDict(datao.public_statistics)
    __nodePropertiesDict(datao.node_properties)

    __contextDescriptionDict_0(datao.contexts[0])
    __contextDescriptionDict_1(datao.contexts[1])

    datao.public_site = "http://www.matrixenter.int"
    datao.hidden_service = "cnwoecowiecnirnio23rn23io.onion"
    datao.url_schema = "/"
    datao.name = "don't track us: AUTOVELOX"


