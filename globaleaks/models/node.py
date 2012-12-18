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

    __storm_table__ = 'systemsettings'

    id = Int(primary=True)

    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    languages = Pickle()

    creation_time = DateTime()

    public_stats_update_time = Int()
    private_stats_update_time = Int()

    @transact
    def configure_node(self, input_block):
        """
        @param input_block: its a totally unmaintainable dict
        @return: None
        """

        store = self.getStore('configure_node')

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            store.close()
            raise NodeNotFound
        if node_data is None:
            store.close()
            raise NodeNotFound

        node_data.description = input_block['description']
        node_data.name = input_block['name']
        node_data.public_site = input_block['public_site']
        node_data.hidden_service = input_block['hidden_service']
        node_data.public_stats_update_time = int(input_block['public_stats_update_time'])
        node_data.private_stats_update_time = int(input_block['private_stats_update_time'])
        node_data.email = input_block['email']
        node_data.languages = input_block['languages']

        log.msg("Updated node main configuration")
        store.commit()
        store.close()

    @transact
    def get_public_info(self):

        store = self.getStore('get_public_info')

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            store.close()
            raise NodeNotFound
        if node_data is None:
            store.close()
            raise NodeNotFound

        # I'd prefer wrap get_admin_info and then .pop() the
        # private variables, but wrap a defered cause you can't return,
        # so would be nice but I don't have clear if workarounds costs too much
        retTmpDict= { 'name' : node_data.name,
                      'description' : node_data.description,
                      'hidden_service' : node_data.hidden_service,
                      'public_site' : node_data.public_site,
                      'public_stats_update_time' : node_data.public_stats_update_time,
                      'email' : node_data.email,
                      'languages' : node_data.languages
                    }

        store.close()
        return retTmpDict

    @transact
    def get_admin_info(self):

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
        retAdminDict= { 'name' : node_data.name,
                        'description' : node_data.description,
                        'hidden_service' : node_data.hidden_service,
                        'public_site' : node_data.public_site,
                        'public_stats_update_time' : node_data.public_stats_update_time,
                        'private_stats_update_time' : node_data.private_stats_update_time,
                        'email' : node_data.email,
                        'languages' : node_data.languages
            }

        store.close()
        return retAdminDict

    @transact
    def initialize_node(self):
        """
        @return: True | False
        This function is called only one time in a node life, and initialize
        the table. the configure_node run edit of this row (id = 1)
        """
        store = self.getStore('first node init')

        onlyNode = Node()

        onlyNode.id = 1
        onlyNode.name = u"Please, set me: name/title"
        onlyNode.description = u"Please, set me: description"
        onlyNode.hidden_service = u"Please, set me: hidden service"
        onlyNode.public_site = u"Please, set me: public site"
        onlyNode.email = u"email@dumnmy.net"
        onlyNode.private_stats_update_time = 30 # minutes
        onlyNode.public_stats_update_time = 120 # minutes
        onlyNode.languages = [ { "code" : "it" , "name": "Italiano"}, { "code" : "en" , "name" : "English" },  {"code" : "vv", "name" : u"ζ Vecnish"} ]

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

        store = self.getStore('only_one')
        nodenum = store.find(Node).count()
        store.close()

        if 1 == nodenum:
            return True
        else:
            print "Unexpected status (exception made for first start), node configured", nodenum
            return False
