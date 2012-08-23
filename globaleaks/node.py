# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from cyclone.util import ObjectDict as OD

lorem = "Letterpress whatever incididunt consequat proident ennui, in post-ironic tofu. Shoreditch banksy four loko, wayfarers mollit brunch minim jean shorts chillwave raw denim squid twee cosby sweater sunt. Farm-to-table authentic sunt, wayfarers DIY cred viral wes anderson lomo aliqua proident. Fingerstache twee mlkshk, williamsburg ea nostrud master cleanse single-origin coffee accusamus pitchfork voluptate skateboard delectus sapiente. Mixtape beard magna semiotics dolor art party. Cray commodo occaecat twee thundercats, viral veniam in. In typewriter vegan, mixtape put a bird on it trust fund ex wayfarers retro commodo semiotics."
footime = '2012-08-23 13:36:30.355617'

groups = [{'id' : 0,
           'name': 'group1',
           'description' : lorem,
           'spoken_language': 'Array, list of spoken languages',
           'tags': 'string',
           'receiver_list': 'Array',
           'associated_module': '$moduleDataDict',
           'creation_date': footime,
           'update_date': footime},
          {'id' : 1,
           'name': 'group2',
           'description' : lorem,
           'spoken_language': 'Array, list of spoken languages',
           'tags': 'string',
           'receiver_list': 'Array',
           'associated_module': '$moduleDataDict',
           'creation_date': footime,
           'update_date': footime}]

fields = [{'name': 'title', 
          'label': 'Title',
          'type': 'string', 
          'hint': 'Insert your title here',
          'default': '',
          'help': 'Place here your help text',
          'required': True},

          {'name': 'description', 
          'label': 'Description',
          'type': 'text', 
          'hint': 'Insert your description here',
          'default': '',
          'help': 'Place here your help text',
          'required': True},

          {'name': 'eyewitness', 
          'label': 'Eye witness?',
          'type': 'checkbox', 
          'help': '',
          'hint': 'check if this applies',
          'required': True},

          {'name': 'othercheckbox', 
          'label': 'Is this true?',
          'type': 'checkbox', 
          'help': '',
          'hint': 'check if this applies',
          'required': False},

          {'name': 'option',
           'label': 'What option?',
           'type': 'radio',
           'help': 'Place here your help text',
           'options': [{'label': 'Option 1', 'value': 'option1'},
                      {'label': 'Option 2', 'value': 'option2'}],
           'hint': 'Pick one of these many options',
           'required': False,
          }
        ]

info = OD()
info.name = "Node Name"
info.statistics = {'x': 20, 'y': 300, 'z': 123}
info.properties = {'x': True, 'y': False}
info.description = lorem
info.https_address = 'https://example.com/'
info.httpo_address = 'httpo://foobar.onion/'

info.contexts = [{'id': 0, 'name': 'context1', 
                  'groups': groups,
                  'fields': fields,
                  'description': lorem,
                  'style': 'default',
                  'creation_date': footime,
                  'update_date': footime},
                 {'id': 1, 'name': 'context2', 
                  'groups': groups,
                  'fields': fields,
                  'description': lorem,
                  'style': 'default',
                  'creation_date': footime,
                  'update_date': footime}]


