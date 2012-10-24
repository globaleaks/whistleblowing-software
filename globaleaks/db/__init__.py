"""
    GLBackend Database
    ******************

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""

# this need to be completed for be included, but no more for be used in the
# createQuery loop

__all__ = ['createTables', 'database', 'transactor']

from twisted.python.threadpool import ThreadPool
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from storm.locals import Store
from storm.uri import URI
from storm.databases.sqlite import SQLite

from globaleaks import database, transactor
from globaleaks.utils import log

@inlineCallbacks
def createTables():
    """
    XXX this is to be refactored and only exists for experimentation.
    This will become part of the setup wizard.
    """
    from globaleaks import models
    from globaleaks.db import tables
    from globaleaks.messages import dummy

    for m in [models.node, models.receiver, models.submission, models.tip, models.admin ]:
        for model_name in m.__all__:
            try:
                model = getattr(m, model_name)
            except Exception, e:
                log.err("Error in db initting")
                log.err(e)
            try:
                log.debug("Creating %s" % model)
                yield tables.runCreateTable(model, transactor, database)
            except Exception, e:
                log.debug(str(e))


    nod = models.node.Node()
    is_only_one = yield nod.only_one()

    if False == is_only_one:
        yield nod.initialize_node()
        # initvals = yield nod.get_admin_info()
        initvals = yield nod.get_public_info()
        print "Node initialized with", initvals

    r = models.receiver.Receiver()
    receiver_count = yield r.count()

    if receiver_count == 0:
        log.debug("Creating dummy receiver tables")
        receiver_dicts = yield r.create_dummy_receivers()
        log.debug(str(receiver_dicts))

    log.msg("# Currently installed receivers")
    for receiver in receiver_dicts:
        log.msg("* %s " % receiver['name'])

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
        log.debug("[!] No contexts. Creating dummy ones!")
        yield c.new(context_dict)
        yield c.new(dummy_context)

    context_dicts = yield c.list_description_dicts()
    log.debug("# We have these contexts:")
    for context in context_dicts:
        log.debug("* %s " % context['name'])

