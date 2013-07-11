"""
The goal of this thing is to migrate something like this:


[
    {"name": {"en": "Short title"},
     "hint": {"en": "Describe your tip-off with a line/title"},
     "required": true,
     "presentation_order": 1,
     "value": "", 
     "key": "Short title",
     "type": "text"
    }, 
    {"name": {"en": "Full description"},
     "hint": {"en": "Describe the details of your tip-off"},
     "required": true,
     "presentation_order": 2,
     "value": "",
     "key": "Full description",
     "type": "text"},
    {"name": {"en": "Files description"},
     "hint": {"en": "Describe the submitted files"},
     "required": false, "presentation_order": 3,
     "value": "",
     "key": "Files description",
     "type": "text"}
]


to This

{'en':
    [{"name": "Short title",
     "hint": "Describe your tip-off with a line/title",
     "required": true,
     "presentation_order": 1,
     "value": "", 
     "key": "Short title",
     "type": "text"
    }, 
    {"name": "Full description"},
     "hint": "Describe the details of your tip-off",
     "required": true,
     "presentation_order": 2,
     "value": "",
     "key": "Full description",
     "type": "text"},
    {"name": "Files description"},
     "hint": "Describe the submitted files",
     "required": false,
     "presentation_order": 3,
     "value": "",
     "key": "Files description",
     "type": "text"}
    ]
}

"""

def get_all_languages(fields):
    all_languages = set()
    for field in fields:
        languages = field['name'].keys()
        for language in languages:
            all_languages.add(language)
    return all_languages

default_fields = [
    {"name": {"en": "Short title"},
     "hint": {"en": "Describe your tip-off with a line/title"},
     "required": True,
     "presentation_order": 1,
     "value": "", 
     "key": "Short title",
     "type": "text"
    }, 
    {"name": {"en": "Full description"},
     "hint": {"en": "Describe the details of your tip-off"},
     "required": True,
     "presentation_order": 2,
     "value": "",
     "key": "Full description",
     "type": "text"},
    {"name": {"en": "Files description"},
     "hint": {"en": "Describe the submitted files"},
     "required": False, "presentation_order": 3,
     "value": "",
     "key": "Files description",
     "type": "text"}
]

def fields_conversion(old_fields):

    default_language = 'en'
    all_languages = get_all_languages(old_fields)
    new_fields = {}
    for language in all_languages:
        new_fields[language] = old_fields
        for idx, _ in enumerate(new_fields[language]):
            try:
                new_fields[language][idx]['name'] = unicode(old_fields[idx]['name'][language])
            except KeyError:
                new_fields[language][idx]['name'] = unicode(old_fields[idx]['name'][default_language])
            try:
                new_fields[language][idx]['hint'] = unicode(old_fields[idx]['hint'][language])
            except KeyError:
                new_fields[language][idx]['hint'] = unicode(old_fields[idx]['hint'][default_language])

    return new_fields
