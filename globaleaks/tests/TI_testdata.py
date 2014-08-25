# -*- coding: UTF-8

# This file only defines the data struct to emulate Transparency International needs

from globaleaks.models import Field, FieldGroup, Step, Context, uuid4
from globaleaks.utils.utility import datetime_to_ISO8601

TI_context = {
    'id': unicode(uuid4()),
    # localized stuff
    'name': u'Already localized name',
    'description': u'Already localized desc',
    # fields, usually filled in content by fill_random_fields
    'steps': [ ],
    'selectable_receiver': False,
    'select_all_receivers': True,
    'tip_max_access': 10,
    # tip_timetolive is expressed in days
    'tip_timetolive': 20,
    # submission_timetolive is expressed in hours
    'submission_timetolive': 48,
    'file_max_download' :1,
    'escalation_threshold': 1,
    'receivers' : [],
    'tags': [],
    'file_required': False,
    'receiver_introduction': u'These are our receivers',
    'fields_introduction': u'These are our fields',
    'postpone_superpower': False,
    'can_delete_submission': False,
    'maximum_selectable_receivers': 0,
    'require_file_description': False,
    'delete_consensus_percentage': 0,
    'require_pgp': False,
    'show_small_cards': False,
    'show_receivers': False,
    'presentation_order': 0,
}

# Transparency Iternational Italy - Anticorruption fields

# This field represent the communication between Client and Backend,
# Will be used to test Handler
# Has to be managed by GLBackend to be converted on the appropriate model
TI_1 = \
    {
        'label' :
            {
                'it': u'Sei un dipendente pubblico o privato ?',
                'en': u'Are you a public or a private employee ?'
            },
        'description' :
            {
                'it' : u"Descrizione - Cosa devo mettere qui ?",
                'en' : u"This is a description - WTF I've to put here ?"
            },
        'hint' :
            {
                'it' : u'Se sei un dipendente pubblico non sarai mai licenziato: complimenti! ಠ_ಠ ',
                'en' : u'ʘ A☭public☭employee☭has☭to☭work☭for☭the☭Nation, ☭ BE PROUD! ʘ'
            },
        'multi_entry' : True,
        'x' : 1,
        'y' : 1,
        'type' : 'checkbox',
        'stats_enabled' : True,
        'required' : True,
        'regexp' : '.*', # this is fine, or just saying 'None' is good ? TODO check
        'options':
            {
                'RANDOMKEY' :
                    {
                        'label': {
                            'it' : u'Dipendente pubblico',
                            'en' : u'Public employee'
                        },
                        'trigger': u'00000000-0000-0000-0000-0000PUBBLICO',
                    },
                'OTHERRANDOM' :
                    {
                        'label': {
                            'it' : u'Dipendente privato',
                            'en' : u'Private employee'
                        },
                        'trigger': u'00000000-0000-0000-0000-00000PRIVATO',
                    }
            },
        'default_value' : True,
        'preview' : False,
    }

TT_2_Public = [

    # This is triggered when a public employee is selected:
    # checkbox "did you have already report to the anticorruption manager ?"
    {
        'label' :
            {
                'it': u"Hai già segnalato l'evento al responsabile anticorruzione ?",
                'en': u"Did you've already report the corruption event to the appropriate person?"
            },
        'description' :
            {
                'it' : u'Il responsabile anticorruzione è Mario Draghi €.',
                'en' : u"The anticorruption manager is Mario Draghi €."
            },
        'hint' :
            {
                'it' : u'Segnalare al responsabile è meglio, ma se ritieni, prosegui',
                'en' : u'ªªªªª did you really really really go hard ?',
            },
        'multi_entry' : True,
        'x' : 0, # They are triggered, so, "0"
        'y' : 0,
        'type' : 'radio',
        'stats_enabled' : True,
        'options':
            {
                'singlerandomid' :
                    {
                        'label': {
                            'it' : u"SI",
                            'en' : u"YES"
                        },
                        'trigger': u'00000000-0000-0000-0000-000SEGNALATO',
                    },
                'otherrandomid' :
                    {
                        'label': {
                            'it' : u"NO",
                            'en' : u"Nope"
                        },
                        'trigger': u'00000000-0000-0000-0000-NONSEGNALATO',
                    }
            }
    }
]

TI_3_Public_Has_Reported = [
    # THIS IS A LIST, with two questions.
    # THEREFORE, we need to put the THIRD one, the 'group'
    #
    # "Qual'è il tuo ente di appartenenza ?"
    # "Quale è stato l’esito della tua segnalazione?"
    #
    # position 0, the 'id' triggered, is the 'group'
    {
        'id': u'00000000-0000-0000-0000-000SEGNALATO',
        'type' : 'group',
        'options' : [
            u'00000000-0000-0000-0000-00000000ente',
            u'00000000-0000-0000-0000-0000000esito',
        ]
    },
    # first one, 'text'
    {
        'id': u'00000000-0000-0000-0000-00000000ente',
        'label' : {
            'it': u"Qual'è il tuo ente di appartenenza ? ",
            'en': u"Which is the name of your department ? "
        },
        'description' : {
            'it' : u"Indica la tua sezione, e se necessario il luogo del reparto",
            'en' : u"Put your departname name, and eventually the address"
        },
        'hint' : {
             'it': u"Molto probabilmente sei in segreteria. Che si mette qui ?",
             'en': u"I don't know what can be put here",
         },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': True,
        'regexp': None,
        'options': {
            'min': 5,
            'max': 100
        },
        'default_value': u'Segreteria generale',
        'preview': True
    },
    # second one, 'text'
    {
        'id': u'00000000-0000-0000-0000-0000000esito',
        'label' : {
            'it': u"Qual'è stato l'esito della tua segnalazione ? ",
            'en': u"Which has been the reports outcome ? ",
        },
        'description' : {
            'it' : u"Descrivi sinteticamente la relazione con il responsabile",
            'en' : u"Report in short your reports history",
        },
        'hint' : {
            'it': u"Se puoi, menziona il numero di pratica e la data della segnalazione",
            'en': u"If you can, put the record number and the data of the report",
            },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': True,
        'regexp': None,
        'options': {
            'min': 0,
            'max': 400
        },
        'default_value': None,
    }
]

TI_4_Public_Has_Not_Reported = [

# SE NO:
# - Modal informativo con scelta “Procedi con la Segnalazione” o “Informa il tuo Responsabile Anticorruzione”
# - SE “Informa il tuo responsabile anticorruzione” -> Apri browser su pagina TI-it
# - SE “Procedi con segnalazione”
#   ->  Quali sono i motivi per cui non hai segnalato al responsabile anticorruzione?
    {
        'id': u'00000000-0000-0000-0000-NONSEGNALATO',
        'type' : 'group',
        'options' : [
            u'00000000-0000-0000-0000-0000000Modal',
            u'00000000-0000-0000-0000-000000motivi',
        ]
    },
    {
        'label' :
            {
                'it': u"Attenzione, la pratica corretta è un'altra",
                'en': u"☢ Warning ☢"
            },
        'link' :
            {
                'it' : u"http://transparency.it/qualcosadibello.html",
                'en' : u"http://transparency.co.uk/somethingtunny.html"
            },
        'description' :
            {
                'it' : u'Segnalare al responsabile è meglio, ma se ritieni, prosegui',
                'en' : u'Is very better if you go to the appropriate human. but is up to you',
                },
        'multi_entry' : True,
        'x' : 0, # They are triggered, so, "0"
        'y' : 0,
        'type' : 'modal',
        'stats_enabled' : False,
        'options':
            {
                'blah_one' :
                    {
                        'label': {
                            'it' : u"Dimmi di più",
                            'en' : u"Get more information"
                        },
                        # did the 'Yes' has to trigger a redirect ?
                        # or is implemented the button with a link ?
                    },
                'blah_two' :
                    {
                        'label': {
                            'it' : u"Procedi comunque",
                            'en' : u"Go for your submission"
                        },
                        # Is this good ?
                        'trigger': u'00000000-0000-0000-0000-000000motivi',
                    }
            }
    },
    {
        # 'trigger': u'00000000-0000-0000-0000-000000motivi',
        'id': u'00000000-0000-0000-0000-000000motivi',
        'label' : {
            'it': u"Come mai non segui la procedura ?",
            'en': u"Why you don't blah ?",
            },
        'description' : {
            'it' : u"Se c'è qualche motivo per cui non vuoi segnalare al responsabile anticorruzione, scrivilo",
            'en' : u" -- --",
            },
        'hint' : {
            'it': u"E' importante per noi conoscere il motivo di una segnalazione al di fuori della procedura, per quanto noi la seguiremo al meglio",
            'en': u" * * * ",
            },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': False, # TODO right ?
        'regexp': None,
        'options': {
            'min': 0,
            'max': 0
        },
        'default_value': None,
    }
]

TT_2_Privato = [
# Hai già segnalato l’illecito internamente alla tua azienda e/o a regolatori di settore? SI/NO
#  SE SI,
#  Quale è l’azienda per cui lavori ?
#   - Quale è stato l’esito della tua segnalazione?
# SE NO,
#   ->  Quali sono i motivi per cui non hai segnalato internamente all’azienda?
    {
        'id': u'00000000-0000-0000-0000-00000PRIVATO',
        'type' : 'group',
        'options' : [
            # only one, also because this trigger another field in this group.
            # just the other field is not immediately show
            u'00000000-0000-0000-0000-GiaSegnalato',
        ]
    },
    {
        'id' : u"00000000-0000-0000-0000-GiaSegnalato",
        "label": {
            'it': u"Hai già segnalato all'azienda in cui lavori ?",
            'en': u" x "
        },
        "description": {
            'it': u"Descrrizione ? ",
            'en': u" ** silly girl ** "
        },
        "hint": {
            'it': u"GO HARD? ",
            'en': u"GO HARD! "
        },
        "multi_entry": True,
        "x": 0,
        "y": 0,
        "type": "checkbox",
        "stats_enabled": True,
        "required": True,
        "regexp": ".*",
        "options":
            {
                "one": {
                    'label' :{
                        "it": u"Si",
                        'en': u"Yes"
                    },
                    'trigger':u"00000000-0000-0000-0000-000SiAZIENDA",
                }
                "two": {
                    'label' :{
                        "it": u"No",
                        'en': u"Nope"
                    },
                    'trigger':u"00000000-0000-0000-0000-000NoAZIENDA",
                }
            },
        "default_value": None,
        "preview": False,
    },
    {
        'id':u"00000000-0000-0000-0000-000SiAZIENDA",
        "label": {
            'it': u"Qual'è stato l'esito della segnalazione",
            'en': u" x "
        },
        "description": {
            'it': u"wtf ?",
            'en': u" ** silly girl ** "
        },
        "hint": {
            'it': u"GO HARD? ",
            'en': u"GO HARD! "
        },
        "multi_entry": False,
        "x": 0,
        "y": 0,
        "type": "text_area",
        "stats_enabled": False,
        "required": False,
        "regexp": ".*",
        "options": {
            'min': 0,
            'max': 2000,
        }
    },
    {
        'id':u"00000000-0000-0000-0000-000NoAZIENDA",
        "label": {
            'it': u"Per quale motivo non hai segnalato all'azienda ?",
            'en': u" x "
        },
        "description": {
            'it': u"??? cosa si può scrivere qui ???",
            'en': u" ** silly girl ** "
        },
        "hint": {
            'it': u"GO HARD? ",
            'en': u"GO HARD! "
        },
        "multi_entry": False,
        "x": 0,
        "y": 0,
        "type": "text_area",
        "stats_enabled": False,
        "required": False,
        "regexp": ".*",
        "options": {
            'min': 0,
            'max': 2000,
        }
    }
]

TI_5_shared = [
#  Hai già segnalato alla polizia o alla autorità giudiziaria?
#  SE SI, (vai allo step "6")
#
# SE NO (vai allo step "7"),

    {
    'label' :
        {
            'it': u"Hai già segnalato all'autorità giudiziaria ?",
            'en': None,
        },
    'description' :
        {
            'it' : u'Se è per servilismo o altri abietti motivi: delatore.',
            'en' : None,
        },
    'hint' :
        {
            'it' : u'Se invece sei un buona fede: vabè',
            'en' : None,
            },
    'multi_entry' : True,
    'x' : 0, # They are triggered, so, "0"
    'y' : 0,
    'type' : 'radio',
    'stats_enabled' : True,
    'options':
        {
            'single1' :
                {
                    'label': {
                        'it' : u"SI",
                        'en' : u"YES"
                    },
                    'trigger': u'00000000-0000-0000-0000-000000segnal',
                },
            'other1' :
                {
                    'label': {
                        'it' : u"NO",
                        'en' : u"Nope"
                    },
                    'trigger': u'00000000-0000-0000-0000-0000ZeRo0DAY',
                }
        }
    }
]

TI_6_delatore = [
#    -> A chi hai effettuato la segnalazione?
#    -> Hai fatto una segnalazione o sporto una denuncia?
#    -> Quale è stato l’esito della tua segnalazione e/o denuncia?
    {
        'id': u'00000000-0000-0000-0000-000000segnal',
        'type': 'group',
        'options' : [
            u'00000000-0000-0000-0000-0000e0000CHI',
            u'00000000-0000-0000-0000-0000e0000SoD',
            u'00000000-0000-0000-0000-0000e00ES1TO'
        ]
    },
    {
        'id': u'00000000-0000-0000-0000-0000e0000CHI',
        'label' : {
            'it': u"A chi hai effettuato la segnalazione?",
            'en': None,
            },
        'description' : {
            'it' : None,
            'en' : None,
            },
        'hint' : {
            'it': None,
            'en': None,
            },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': False,
        'regexp': None,
        'options': {
            'min': 0,
            'max': 0
        },
        'default_value': None,
    },
    {
        'id': u'00000000-0000-0000-0000-0000e0000SoD',
        'label' : {
            'it': u"Hai fatto una segnalazione o sporto una denuncia?",
            'en': None,
            },
        'description' : {
            'it' : None,
            'en' : None,
            },
        'hint' : {
            'it': None,
            'en': None,
            },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': False,
        'regexp': None,
        'options': {
            'min': 0,
            'max': 0
        },
        'default_value': None,
    },
    {
        'id': u'00000000-0000-0000-0000-0000e00ES1TO',
        'label' : {
            'it': u"Quale è stato l’esito della tua segnalazione e/o denuncia?",
            'en': None,
            },
        'description' : {
            'it' : None,
            'en' : None,
            },
        'hint' : {
            'it': None,
            'en': None,
            },
        'multi_entry' : False,
        'x' : 0, # when is 0, mean that is *triggered* and not showed since the begin
        'y' : 0, # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        'type' : 'text',
        'stats_enabled': False,
        'required': False,
        'regexp': None,
        'options': {
            'min': 0,
            'max': 0
        },
        'default_value': None,
    },
]

TI_7_non_delatore = [
#    -> Dialog informativo con scelta “Procedi con la Segnalazione” o “Rivolgiti alla autorità giudiziaria”
#    ->  Quali sono i motivi per cui non hai fatto segnalazione o denuncia all’autorità giudiziaria?
]

