# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting
from globaleaks.tests import helpers
from globaleaks.handlers import wizard

appdata_blob = {
   'version':1,
   'node': {
     'subtitle': { 'en': 'subtitle bello'},
     'footer': { 'en': 'footer brutto'},
     'presentation': { 'en': 'presentation cattivo'},
     'terms_and_conditions': { 'en': 'terms_and_conditions malevoli'}
   },
   'fields': [
     {
       'incremental_number':0,
       'localized_name': {'en':'name','it':'nome'},
       'localized_hint': {'en':'thenameofthesubject','it':'ernomedeltizio'},
       'type':'text',
       'trigger':[1,2],
       'defined_options':None,
     },
     {
       'incremental_number':1,
       'localized_name': {'en':'role','it':'ruolo'},
       'localized_hint':{'en':'theroleofthesubject','it':'ertitolodeltizio'},
       'type':'radio',
       'trigger':[],
       'defined_options':[
          { 'order':1, 'value':'a', 'localized_name':
            {'en':'chief','it':'capo'}},
          { 'order':2, 'value':'b', 'localized_name':
            {'en':'slave','it':'schiavo'}},
          { 'order':3, 'value':'c', 'localized_name':
            {'en':'consultant','it':'consulente'}}
       ]
     },
     {
       'incremental_number':2,
       'localized_name':{'en':'departement','it':'dipartimento'},
       'localized_hint':{'en':'thedepartmentwiththeissue','it':'dipartimento'},
       'type':'radio',
       'trigger':[],
       'defined_options':[
          { 'order':1,'value':'a', 'localized_name':
            { 'en':'marketing','it':'pubblicitari'}},
          { 'order':2,'value':'b', 'localized_name':
            { 'en':'informationtechnology','it':'inerd!'}}
       ]
     }
   ]
}

class TestWizardCollection(helpers.TestHandler):
    _handler = wizard.AppdataCollection

    @inlineCallbacks
    def test_post(self):

        handler = self.request(appdata_blob, role='admin')
        yield handler.post()

        appdata_blob['version'] = (appdata_blob['version'] + 1)

        handler = self.request(appdata_blob, role='admin')
        yield handler.post()

        yield handler.get()
        self.assertEqual(len(self.responses), len(appdata_blob['fields']) )
        self.assertEqual(self.responses[2]['version'], appdata_blob['version'])


class TestFirstSetup(helpers.TestHandler):
    _handler = wizard.FirstSetup

    @inlineCallbacks
    def test_post(self):

        # FIX currently wizard create contexts only with default fields
        # so only valid requests are the one with steps = []
        self.dummyContext['steps'] = []

        wizard_blob = {
            'receiver' : self.get_dummy_receiver("christianice"),
            'fields' : self.dummyFields,
            'context' : self.dummyContext,
            'node' : self.dummyNode,
            'appdata' : appdata_blob,
        }

        handler = self.request(wizard_blob, role='admin')
        yield handler.post()