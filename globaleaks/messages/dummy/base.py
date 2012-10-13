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
        "filename": u'passwd.txt',
        "file_description": u'a list of encrypted password',
        "size": 4242,
        "content_type": u'plain/text',
        # datao.date
        "cleaned_meta_data": False
        })

fileDicts.append({
        "filename": u'antani.pdf',
        "file_description": u'a list of terrible secrets',
        "size": 3231,
        "content_type": u'application/pdf',
        # datao.date
        "cleaned_meta_data": True
        })


folderDict = {"folder_id": idops.random_folder_id(),
        "folder_name": u'those from my chief personal USB key',
        "folder_description": u'He left the key in the office, does not contain jobs files, but some proof that is a Mafia thug',
        "download_performed": 2,
        "files": fileDicts}

receiverDescriptionDicts = []

receiverDescriptionDicts.append({
        "id": idops.random_receiver_id(),
        "can_delete_submission": True,
        "can_postpone_expiration": True,
        "can_configure_notification": True,
        "can_configure_delivery": True,
        "can_trigger_escalation": True,
        "name": u'cool antivelox organization',
        "description": u'we\'re fighting against wrong penalities since 1492',

        # one language is the default
        "languages_supported": ["IT", "ES"]
        })


receiverDescriptionDicts.append({
    "id": idops.random_receiver_id(),
    "can_delete_submission": True,
    "can_postpone_expiration": True,
    "can_configure_notification": True,
    "can_configure_delivery": True,
    "can_trigger_escalation": True,

    "name": u'the police chief',
    "description": u'we\'re the police chief, we\'re the law',

    # one language is the default
    "languages_supported": ["IT", "EN"]
    })

receiverDescriptionDicts.append({
    "id": idops.random_receiver_id(),

    "can_delete_submission": False,
    "can_postpone_expiration": False,
    "can_configure_notification": True,
    "can_configure_delivery": False,
    "can_trigger_escalation": False,

    "name": u'the police thug',
    "description": u'we can close our eyes if an autovelox is reported to be wrong',
    "languages_supported": ["IT", "ES"]
    })

receiverDescriptionDicts.append({
    "id": idops.random_receiver_id(),

    "can_delete_submission": False,
    "can_postpone_expiration": False,
    "can_configure_notification": True,
    "can_configure_delivery": False,
    "can_trigger_escalation": False,

    "name": u'the guys with painting rifle',
    "description": u'we can close the eyes of the autovelox',

    "languages_supported": ["IT", "ES"]
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
    "name": u'city',
    "label": u'city',
    "required": True,
    "hint": u'the city of the autovelox',
    "value": u'this is the default value',
    "type": u'string',
    })

formFieldsDicts.append({
    "presentation_order": 2,
    "label": u'road',
    "name": u'road',
    "required": True,
    "hint": u'the road where the autovelox is running',
    "value": u'this is the default value',
    "type": u'string',
    })

formFieldsDicts.append({
    "presentation_order": 3,
    "label": u'penality details',
    "name": u'dict2',
    "required": True,
    "hint": u'put the number of the penality',
    "value": u'this is the default value',
    "type": u'string',
    })

formFieldsDicts.append({
    "presentation_order": 4,
    "label": u'how do you know that ?',
    "name": u'dict3',
    "required": False,
    "hint": u'details: eg, do you present your case to a judge ?',
    "value": u'this is the default value',
    "type": u'text',
    })

moduleDataDict_N = {
    "module_id": idops.random_module_id(),
    "active": True,
    "module_type": u'notification',
    "name": u'Encrypted E-Mail',
    "module_description": u'with this module you can setup your own GPG key'\
                          'and receive safely the notice of a new tip, and'\
                          'your secret link',

    # --------------------------------------------------------------
    # "service_message": u'Invalid Public Key provided"
    # "service_message": u'Your PGP key is correctly configured"
    "service_message": u'You have not yet configured your PGP key'
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
    "module_id": idops.random_module_id(),
    "active": True,
    "module_type": u'delivery',
    "name": u'upload in FTP',
    "module_description": u'with this module, you can found the data in your personal FTP',

    "service_message": u'The latest time a delivery has been sent, it worked!',

    # XXX not sure what this is about
    # _formFieldsDict0("admin_options[0])
    # _formFieldsDict1("user_options[0])
    }


"""
remind: are declared FOUR fields by base
"""
contextDescriptionDicts = []

contextDescriptionDicts.append({
    "context_id": idops.random_context_id(),
    "name":"Autovelox broken",
    "description": u'tell us which autovelox is working bad, we\'re tired of wrong fines!',
    # "creation_date", "time"
    # "append_date", "time"

    # only 1 form is *required*, other can be expanded
    "fields": formFieldsDicts,

    "selectable_receiver": False,
    "receivers": receiverDescriptionDicts,
    "escalation_threshold": 4,
    "languages_supported": ['EN']
    })


contextDescriptionDicts.append(contextDescriptionDicts[0].copy())

commentDescriptionDict = {
    "writtentext": u'Hello, I\'ve readed your stuff, I like it',
    "commenttype": u'receiver',
    "author": u'Julian Hussein Manning',
    # date ? default
    }

tipSubIndex = {
    "tID": idops.random_tip_id(),
    "tip_title": u'Greatest secret of all world - Enter the ninja',

    "notification_adopted": u'default email',
    "delivery_adopted": u'default download',

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


