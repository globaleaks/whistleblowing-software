"""
    GLBackend Database
    ******************

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""

# __all__ = ['models', 'tips', 'admin', 'receiver', 'submission'  ]

# this need to be completed for be included, but no more for be used in the
# createQuery loop

__all__ = ['getStore', 'createTables', 'database', 'transactor']

"""
Quick reference for the content:

    base:        TXModel
    tips:        StoredData, Folders, Files, Comments, SpecialTip
    admin:       SytemSettings, Contexts, ModulesProfiles, ReceiversInfo, AdminStats, LocalizedTexts
    receiver:    PersonalPreference, ReceiverTip
    submission:  Submission, PublicStats

"""

from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from storm.twisted.transact import Transactor, transact
from storm.locals import *
from storm.uri import URI
from storm.databases.sqlite import SQLite

# File sqlite database
database_uri = 'sqlite:///globaleaks.db'
# In memory database
# database_uri = 'sqlite:'

database = SQLite(URI(database_uri))

threadpool = ThreadPool(0, 10)
threadpool.start()
transactor = Transactor(threadpool)

def getStore():
    s = Store(database)
    return s

@inlineCallbacks
def createTables():
    """
    XXX this is to be refactored and only exists for experimentation.
    This will become part of the setup wizard.
    """
    from globaleaks import models
    from globaleaks.db import tables
    from globaleaks.messages import dummy

    for m in [models.receiver, models.submission, models.tip, models.admin]:
        for model_name in m.__all__:
            try:
                model = getattr(m, model_name)
            except Exception, e:
                print e
            try:
                print "Creating %s" % model
                yield tables.runCreateTable(model, transactor, database)
            except Exception, e:
                print e
                print "Failed. Probably the '%s' table exists." % model_name
    print "In her et0"
    r = models.receiver.Receiver()
    receiver_dicts = yield r.receiver_dicts()

    if not receiver_dicts:
        print "Creating dummy receiver tables"
        receiver_dicts = yield r.create_dummy_receivers()

    print "These are the the installed receivers:"
    for receiver in receiver_dicts:
        print "-----------------"
        print receiver
        print "-----------------"

    c = models.admin.Context()
    context_dict = {"name": u"Random Context",
            "description": u"Test description",
            "selectable_receiver": True,
            "escalation_threshold": 10,
            "languages_supported": [u'ENG', u'ITA'],
            "fields": dummy.base.formFieldsDicts2,
            "receivers": receiver_dicts,
    }
    dummy_context = dummy.base.contextDescriptionDicts[0].copy()
    dummy_context['receivers'] = receiver_dicts
    context_dicts = yield c.list_description_dicts()
    if len(context_dicts) == 0:
        print "No contexts. Creating dummy ones!"
        yield c.new(context_dict)
        yield c.new(dummy_context)

    context_dicts = yield c.list_description_dicts()
    print "We have these contexts:"
    for context in context_dicts:
        print "#### %s ####" % context['name']
        print context

