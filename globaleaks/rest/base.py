# -*- coding: UTF-8
#
#   rest/base
#   *********
#
#   Contains all the logic handle input and output validation.

uuid_regexp         = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
receiver_img_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).png'

dateType = r'(.*)'
# contentType = r'(application|audio|text|video|image)'
# via stackoverflow:
# /^(application|audio|example|image|message|model|multipart|text|video)\/[a-zA-Z0-9]+([+.-][a-zA-z0-9]+)*$/
contentType = r'(.*)'

fileDict = {
            "name": unicode,
            "description": unicode,
            "size": int,
            "content_type": contentType,
            "date": dateType,
}

formFieldsDict = {
            "key": unicode,
            "presentation_order": int,
            "name": unicode,
            "required": bool,
            "preview": bool,
            "hint": unicode,
            "type": unicode
}
