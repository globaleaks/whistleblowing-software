from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import idops

"""
What's follow are the GLTypes base, filled with plausible buzzwords, usable by the
dummy requests/answers files
"""

def _publicStatisticsDict(datao):

    datao.active_contexts = 2
    datao.active_receivers = 3
    datao.uptime_days = 100


def _nodePropertiesDict(datao):

    datao.AnonymousSubmissionOnly = True


def _fileDict1(datao):

    datao.filename = "passwd.txt"
    datao.file_description = "a list of encrypted password"
    datao.size = 4242
    datao.content_type = "plain/text"
    # datao.date
    datao.cleaned_meta_data = False

def _fileDict2(datao):

    datao.filename = "antani.pdf"
    datao.file_description = "a list of terrible secrets"
    datao.size = 3231
    datao.content_type = "application/pdf"
    # datao.date
    datao.cleaned_meta_data = True


def _folderDict(datao):

    datao.fID = idops.random_folder_id()
    datao.folder_name = "those from my chief personal USB key"
    datao.folder_description = "He left the key in the office, does not contain jobs files, but some proof that is a Mafia thug"
    datao.download_performed = 2

    # one is sure
    _FileDict(datao.files[0])
    datao.files.append( GLT.fileDict() )
    _FileDict(datao.files[1])


def _receiverDescriptionDict0(datao):

    datao.rID = idops.random_receiver_id()
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


def _receiverDescriptionDict1(datao):

    datao.rID = idops.random_receiver_id()
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


def _receiverDescriptionDict2(datao):

    datao.rID = idops.random_receiver_id()
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


def _receiverDescriptionDict3(datao):

    datao.rID = idops.random_receiver_id()
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


def _adminStatisticsDict(datao):

    datao.hours_interval = 3
    datao.download_number = 30
    datao.receiver_accesses = 40
    datao.submission_received = 2


def _formFieldsDict0(datao):

    datao.presentation_order = 1
    datao.name = "city"
    datao.label = "city"
    datao.required = True
    datao.hint = "the city of the autovelox"
    datao.value = "this is the default value"
    datao.type = "text"


def _formFieldsDict1(datao):

    datao.presentation_order = 2
    datao.label = "road"
    datao.name = "road"
    datao.required = True
    datao.hint = "the road where the autovelox is running"
    datao.value = "this is the default value"
    datao.type = "text"


def _formFieldsDict2(datao):

    datao.presentation_order = 3
    datao.label = "penality details"
    datao.name = "dict2"
    datao.required = True
    datao.hint = "put the number of the penality"
    datao.value = "this is the default value"
    datao.type = "int"


def _formFieldsDict3(datao):

    datao.presentation_order = 4
    datao.label = "how do you know that ?"
    datao.name = "dict3"
    datao.required = False
    datao.hint = "details: eg, do you present your case to a judge ?"
    datao.value = "this is the default value"
    datao.type = "text"


def _moduleDataDict_N(datao):

    datao.mID = idops.random_module_id()
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

    _formFieldsDict0(datao.admin_options[0])
    _formFieldsDict1(datao.user_options[0])


def _moduleDataDict_D(datao):

    datao.mID = idops.random_module_id()
    datao.active = True
    datao.module_type = "delivery"
    datao.name = "upload in FTP"
    datao.module_description = "with this module, you can found the data in your personal FTP"

    datao.service_message = "The latest time a delivery has been sent, it worked!"

    _formFieldsDict0(datao.admin_options[0])
    _formFieldsDict1(datao.user_options[0])


"""
remind: are declared FOUR fields by base
"""
def _contextDescriptionDict0(datao):

    datao.cID = idops.random_context_id()
    datao.name ="Autovelox broken"
    datao.context_description = "tell us which autovelox is working bad, we're tired of wrong fines!"
    # "creation_date", "time"
    # "append_date", "time"

    # only 1 form is *required*, other can be expanded
    _formFieldsDict0(datao.fields[0])

    datao.fields.append ( GLT.formFieldsDict() )
    _formFieldsDict1(datao.fields[1])
    datao.fields.append ( GLT.formFieldsDict() )
    _formFieldsDict2(datao.fields[2])
    datao.fields.append ( GLT.formFieldsDict() )
    _formFieldsDict3(datao.fields[3])

    datao.SelectableReceiver = False

    datao.receivers.append ( GLT.receiverDescriptionDict() )
    _receiverDescriptionDict0(datao.receivers[0])
    datao.receivers.append ( GLT.receiverDescriptionDict() )
    _receiverDescriptionDict1(datao.receivers[1])
    datao.receivers.append ( GLT.receiverDescriptionDict() )
    _receiverDescriptionDict2(datao.receivers[2])
    datao.receivers.append ( GLT.receiverDescriptionDict() )
    _receiverDescriptionDict3(datao.receivers[3])

    datao.EscalationTreshold = 4

    # this would be derived by the mix of the supported
    # language in the receivers corpus
    datao.LanguageSupported.append( "string ")
    datao.LanguageSupported[0] = "EN"


def _contextDescriptionDict1(datao):
    _contextDescriptionDict0(datao)


def _commentDescriptionDict(datao):

    datao.writtentext = "Hello, I've readed your stuff, I like it"
    datao.commenttype = "receiver"
    datao.author = "Julian Hussein Manning"
    # date ? default


def _tipIndexDict(datao):

    datao.cID = idops.random_context_id()

    datao.tiplist.append( GLT.tipSubIndex() )
    _tipSubIndex(datao.tiplist[0])


def _tipSubIndex(datao):

    datao.tID = idops.random_tip_id()
    datao.tip_title = "Greatest secret of all world - Enter the ninja"

    datao.notification_adopted = "default email"
    datao.delivery_adopted = "default download"

    datao.download_limit = 5
    datao.access_limit = 100
    datao.access_performed = 33

    # default "expiration_date"
    # idem "creation_date"
    # idem "last_append_date"

    datao.comment_number = 4
    datao.folder_number = 2
    datao.overall_pertinence = 101


def _tipDetailsDict(datao):

    _tipSubIndex(datao.tip)

    datao.tip_data.append( GLT.formFieldsDict() )
    _formFieldsDict3(datao.tip_data[0])

    datao.folder.append( GLT.fileDict() )
    _fileDict(datao.folder[0])

    datao.comment.append( GLT.commentDescriptionDict() )
    _commentDescriptionDict(datao.comment[0])

    datao.receiver_selected.append( GLT.receiverDescriptionDict() )
    _receiverDescriptionDict0(datao.receiver_selected)


def _localizationDict(datao):
    pass


