# -*- encoding: utf-8 -*-
#
# :authors: Claudio Agosti, Arturo Filastò
# :licence: see LICENSE

from globaleaks.utils import idops

"""
What's follow are the GLTypes base, filled with plausible buzzwords, usable by the
dummy requests/answers files
"""

publicStatisticsDict = {"active_contexts": 2,
        "active_receivers": 3,
        "uptime_days": 100}


nodePropertiesDict = {"anonymous_submission_only": True}


fileDicts = []

fileDicts.append({
        "filename": 'passwd.txt',
        "file_description": 'a list of encrypted password',
        "size": 4242,
        "content_type": 'plain/text',
        # datao.date
        "cleaned_meta_data": False
        })

fileDicts.append({
        "filename": 'antani.pdf',
        "file_description": 'a list of terrible secrets',
        "size": 3231,
        "content_type": 'application/pdf',
        # datao.date
        "cleaned_meta_data": True
        })


folderDict = {"fID": idops.random_folder_id(),
        "folder_name": 'those from my chief personal USB key',
        "folder_description": 'He left the key in the office, does not contain jobs files, but some proof that is a Mafia thug',
        "download_performed": 2,
        "files": fileDicts}

receiverDescriptionDicts = []

receiverDescriptionDicts.append({
        "rID": idops.random_receiver_id(),
        "can_delete_submission": True,
        "can_postpone_expiration": True,
        "can_configure_notification": True,
        "can_configure_delivery": True,
        "can_trigger_escalation": True,
        "receiver_name": "cool antivelox organization",
        "receiver_description": "we're fighting against wrong penalities since 1492",

        # one language is the default
        "language_supported": ["IT", "ES"]
        })


receiverDescriptionDicts.append({
    "rID": idops.random_receiver_id(),
    "can_delete_submission": True,
    "can_postpone_expiration": True,
    "can_configure_notification": True,
    "can_configure_delivery": True,
    "can_trigger_escalation": True,

    "receiver_name": "the police chief",
    "receiver_description": "we're the police chief, we're the law",

    # one language is the default
    "language_supported": ["IT", "EN"]
    })

receiverDescriptionDicts.append({
    "rID": idops.random_receiver_id(),

    "can_delete_submission": False,
    "can_postpone_expiration": False,
    "can_configure_notification": True,
    "can_configure_delivery": False,
    "can_trigger_escalation": False,

    "receiver_name": "the police thug",
    "receiver_description": "we can close our eyes if an autovelox is reported to be wrong",
    "language_supported": ["IT", "ES"]
    })

receiverDescriptionDicts.append({
    "rID": idops.random_receiver_id(),

    "can_delete_submission": False,
    "can_postpone_expiration": False,
    "can_configure_notification": True,
    "can_configure_delivery": False,
    "can_trigger_escalation": False,

    "receiver_name": "the guys with painting rifle",
    "receiver_description": "we can close the eyes of the autovelox",

    "language_supported": ["IT", "ES"]
    })

adminStatisticsDict = {
    "hours_interval": 3,
    "download_number": 30,
    "receiver_accesses": 40,
    "submission_received": 2,
    }

formFieldsDicts = []
formFieldsDicts.append({
    "presentation_order": 1,
    "name": "city",
    "label": "city",
    "required": True,
    "hint": "the city of the autovelox",
    "value": "this is the default value",
    "type": "text",
    })

formFieldsDicts.append({
    "presentation_order": 2,
    "label": "road",
    "name": "road",
    "required": True,
    "hint": "the road where the autovelox is running",
    "value": "this is the default value",
    "type": "text",
    })

formFieldsDicts.append({
    "presentation_order": 3,
    "label": "penality details",
    "name": "dict2",
    "required": True,
    "hint": "put the number of the penality",
    "value": "this is the default value",
    "type": "int",
    })

formFieldsDicts.append({
    "presentation_order": 4,
    "label": "how do you know that ?",
    "name": "dict3",
    "required": False,
    "hint": "details: eg, do you present your case to a judge ?",
    "value": "this is the default value",
    "type": "text",
    })

moduleDataDict_N = {
    "mID": idops.random_module_id(),
    "active": True,
    "module_type": "notification",
    "name": "Encrypted E-Mail",
    "module_description": "with this module you can setup your own GPG key"\
                          "and receive safely the notice of a new tip, and"\
                          "your secret link",

    # --------------------------------------------------------------
    # "service_message": "Invalid Public Key provided"
    # "service_message": "Your PGP key is correctly configured"
    "service_message": "You have not yet configured your PGP key"
    # those was the first three "service_message" that come in mind,
    # this field act as report/error/status message from the module to
    # the users.
    # this message is not displayed to the administrator
    #
    # XXX not sure what this is about
    # _formFieldsDict0("admin_options[0])
    # _formFieldsDict1("user_options[0])
    }


moduleDataDict_D = {
    "mID": idops.random_module_id(),
    "active": True,
    "module_type": "delivery",
    "name": "upload in FTP",
    "module_description": "with this module, you can found the data in your personal FTP",

    "service_message": "The latest time a delivery has been sent, it worked!",

    # XXX not sure what this is about
    # _formFieldsDict0("admin_options[0])
    # _formFieldsDict1("user_options[0])
    }


"""
remind: are declared FOUR fields by base
"""
contextDescriptionDicts = []

contextDescriptionDicts.append({
    "cID": idops.random_context_id(),
    "name":"Autovelox broken",
    "context_description": "tell us which autovelox is working bad, we're tired of wrong fines!",
    # "creation_date", "time"
    # "append_date", "time"

    # only 1 form is *required*, other can be expanded
    "fields": formFieldsDicts,

    "selectable_receiver": False,
    "receviers": receiverDescriptionDicts,
    "escalation_threshold": 4,
    "language_supported": ['EN']
    })


contextDescriptionDicts.append(contextDescriptionDicts[0].copy())

commentDescriptionDict = {
    "writtentext": "Hello, I've readed your stuff, I like it",
    "commenttype": "receiver",
    "author": "Julian Hussein Manning",
    # date ? default
    }

tipSubIndex = {
    "tID": idops.random_tip_id(),
    "tip_title": "Greatest secret of all world - Enter the ninja",

    "notification_adopted": "default email",
    "delivery_adopted": "default download",

    "download_limit": 5,
    "access_limit": 100,
    "access_performed": 33,

    # default "expiration_date"
    # idem "creation_date"
    # idem "last_append_date"

    "comment_number": 4,
    "folder_number": 2,
    "overall_pertinence": 101}

tipIndexDict = {
    "cID": idops.random_context_id(),
    "tiplist": tipSubIndex
    }

tipDetailsDict = {
    "tip_data": [],
    "folder": [],
    "comment": commentDescriptionDict,
    "receiver_selected": [receiverDescriptionDicts[0]],
    }

localizationDict = {}


