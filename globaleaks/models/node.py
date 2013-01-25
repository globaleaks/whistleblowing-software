# -*- coding: UTF-8
#
#   models/node
#   ***********
#
# Manage the single table containing all the node general information,
# can be accessed with different privileges (admin and unprivileged).

from storm.exceptions import NotOneError

from storm.twisted.transact import transact

from storm.store import AutoReload
from storm.locals import Int, Pickle, Unicode, DateTime

from globaleaks.models.base import TXModel
from globaleaks.utils import log
from globaleaks.rest.errors import NodeNotFound

__all__ = [ 'Node' ]


class Node(TXModel):
    """
    This table has only one instance, has the "id", but would not exists a second element
    of this table. This table acts, more or less, like the configuration file of the previous
    GlobaLeaks release (and some of the GL 0.1 details are specified in Context)

    This table represent the System-wide settings
    """

    __storm_table__ = 'systemsettings'

    id = Int(primary=True, default=AutoReload)

    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    languages = Pickle()
    creation_time = DateTime()

    # Here is set the time frame for the stats publicly exported by the node.
    # Expressed in hours
    stats_update_time = Int()
    # The frequency of stats COLLECTION, is defined in context, and the admin
    # see Context separated stats.

    @transact
    def configure(self, input_dict):
        """
        @param input_dict: input dictionary
        @return: None
        """

        store = self.getStore()
        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            raise NodeNotFound
        if node_data is None:
            raise NodeNotFound

        cls_info = get_cls_info(Node)
        for name in cls_info.attributes.iterkeys():
            if name in input_dict:
                setattr(node_data, name, input_dict[name])

        log.msg("Updated node main configuration")

    @transact
    def get(self):

        store = self.getStore()

        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            raise NodeNotFound
        if node_data is None:
            raise NodeNotFound

        retDict= { 'name' : unicode(node_data.name),
                   'description' : unicode(node_data.description),
                   'hidden_service' : unicode(node_data.hidden_service),
                   'public_site' : unicode(node_data.public_site),
                   'stats_update_time' : int(node_data.stats_update_time),
                   'email' : unicode(node_data.email),
                   'languages' : unicode(node_data.languages)
            }
        return retDict
