# -*- coding: utf-8 -*-

from . import Node, Static_L10N

class Node_L10N(object):

  def __init__(self, store, node, trans={}):
    self.store = store
    self.node = node

    en = {
        'footer': 'Powered by GL',
        'whistleblowing_button': 'grow the gristle',
        'security_awarness_text': 'Be careful!',
    }
    self.translations = {'en': en, 'de': en}

  def place_defaults(self):
    self.translations


    for lang, dct in self.translations.iteritems():
      for k, val in dct.iteritems():
        entry = Static_L10N('node', lang, k, val)
        self.store.add(entry)

  def retrieve_lang(self, lang):
    return self.store.find(Static_L10N, Static_L10N.lang == unicode(lang))

