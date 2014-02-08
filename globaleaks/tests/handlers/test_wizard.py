# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import wizard

fields_blob = {
   "version":1,
   "fields": [
     {
       "incremental_number":0,
       "localized_name": {"en":"name","it":"nome"},
       "localized_hint": {"en":"thenameofthesubject","it":"ernomedeltizio"},
       "type":"text",
       "trigger":[1,2],
       "defined_options":None,
     },
     {
       "incremental_number":1,
       "localized_name": {"en":"role","it":"ruolo"},
       "localized_hint":{"en":"theroleofthesubject","it":"ertitolodeltizio"},
       "type":"radio",
       "trigger":[],
       "defined_options":[
          { "order":1, "value":"a", "localized_name":
            {"en":"chief","it":"capo"}},
          { "order":2, "value":"b", "localized_name":
            {"en":"slave","it":"schiavo"}},
          { "order":3, "value":"c", "localized_name":
            {"en":"consultant","it":"consulente"}}
       ]
     },
     {
       "incremental_number":2,
       "localized_name":{"en":"departement","it":"dipartimento"},
       "localized_hint":{"en":"thedepartmentwiththeissue","it":"dipartimento"},
       "type":"radio",
       "trigger":[],
       "defined_options":[
          { "order":1,"value":"a", "localized_name":
            { "en":"marketing","it":"pubblicitari"}},
          { "order":2,"value":"b", "localized_name":
            { "en":"informationtechnology","it":"inerd!"}}
       ]
     }
   ]
}

class TestWizardCollection(helpers.TestHandler):
    _handler = wizard.FieldsCollection

    @inlineCallbacks
    def test_post(self):

        handler = self.request(fields_blob, role='admin')
        yield handler.post()

        fields_blob['version'] = (fields_blob['version'] + 1)

        handler = self.request(fields_blob, role='admin')
        yield handler.post()

        yield handler.get()
        self.assertEqual(len(self.responses), len(fields_blob['fields']) )
        self.assertEqual(self.responses[2]['version'], fields_blob['version'])
