# -*- coding: UTF-8
#
#   models/node
#   ***********
#
# Manage the single table containing all the node general information,
# can be accessed with different privileges (admin and unprivileged).

from storm.exceptions import NotOneError

from storm.twisted.transact import transact

from storm.locals import Int, Pickle
from storm.locals import Unicode, DateTime

from globaleaks.models.base import TXModel
from globaleaks.utils import log
from globaleaks.rest.errors import NodeNotFound

__all__ = [ 'Node' ]


class Node(TXModel):
    """
    This table has only one instance, has the "id", but would not exists a second element
    of this table. This table act, more or less, like the configuration file of the previous
    GlobaLeaks release (and some of the GL 0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class Node")
    __storm_table__ = 'systemsettings'

    id = Int(primary=True)

    properties = Pickle()
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()

    creation_time = DateTime()

    public_stats_delta = Int()
    private_stats_delta = Int()

    # XXX To be implemented with APAF: public_key,

    # XXX to be partially specified: leakdirectory_entry

    # XXX missing: languages

    # XXX public site would not be "tor2web domain conversion" but the
    # URL of the initiative in the Internet, like, the blog or the
    # newspaper.

    # XXX tor2web would be a list of translated t2w domain, with a certain
    #     priority

    @transact
    def configure_node(self, input_block):
        """
        @param input_block: its a totally unmaintainable dict
        @return: None
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "configure_node", input_block)

        store = self.getStore('configure_node')

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            store.close()
            raise NodeNotFound
        if node_data is None:
            store.close()
            raise NodeNotFound

        # node_data.properties
        node_data.description = input_block['description']
        node_data.name = input_block['name']
        node_data.public_site = input_block['public_site']
        node_data.hidden_service = input_block['hidden_service']
        node_data.public_stats_delta = int(input_block['public_stats_delta'])
        node_data.private_stats_delta = int(input_block['private_stats_delta'])

        log.msg("Updated node main configuration")
        store.commit()
        store.close()

    @transact
    def get_public_info(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get_public_info")

        store = self.getStore('get_public_info')

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            store.close()
            raise NodeNotFoundError
        if node_data is None:
            store.close()
            raise NodeNotFoundError

        # I'd prefer wrap get_admin_info and then .pop() the
        # private variables, but wrap a defered cause you can't return,
        # so would be nice but I don't have clear if workarounds costs too much
        retTmpDict = {'name' : node_data.name,
                        'description' : node_data.description,
                        'hidden_service' : node_data.hidden_service,
                        'public_site' : node_data.public_site,
                        'public_stats_delta' : node_data.public_stats_delta,
                    }

        store.commit()
        store.close()
        return retTmpDict

    @transact
    def get_admin_info(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "get_admin_info")

        store = self.getStore('get_admin_info')

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            store.close()
            raise NodeNotFound
        if node_data is None:
            store.close()
            raise NodeNotFound

        # this unmaintainable crap need to be removed in the future,
        # and the dict/output generation shall not be scattered
        # around here.
        retAdminDict= {'name' : node_data.name,
                'description' : node_data.description,
                'hidden_service' : node_data.hidden_service,
                'public_site' : node_data.public_site,
                'public_stats_delta' : node_data.public_stats_delta,
                'private_stats_delta' : node_data.private_stats_delta }

        store.commit()
        store.close()
        return retAdminDict

    @transact
    def list_contexts(self):
        pass

    @transact
    def initialize_node(self):
        """
        @return: True | False
        This function is called only one time in a node life, and initialize
        the table. the configure_node run edit of this row (id = 1)
        """
        store = self.getStore('initialize_node')

        onlyNode = Node()

        onlyNode.id = 1
        onlyNode.name = u"uncofigured name"
        onlyNode.description = u"unconfigured description"
        onlyNode.hidden_service = u"unconfigured hidden service"
        onlyNode.public_site = u"unconfigured public site"
        onlyNode.private_stats_delta = 30 # minutes
        onlyNode.public_stats_delta = 120 # minutes

        store.add(onlyNode)
        store.commit()
        store.close()

    @transact
    def only_one(self):
        """
        @rtype : bool
        @return: True or False
        check if the table in Node is only one
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Node", "only_one")

        store = self.getStore('only_one')
        nodenum = store.find(Node).count()
        store.commit()
        store.close()

        if 1 == nodenum:
            return True
        else:
            print "Unexpected status (exception made for first start), node configured", nodenum
            return False
