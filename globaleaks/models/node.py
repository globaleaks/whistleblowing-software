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
    of this table. This table acts, more or less, like the configuration file of the previous
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
    def get_public_info(self):

        store = self.getStore()
        try:
            node_data = store.find(Node, 1 == Node.id).one()
        except NotOneError:
            raise NodeNotFound
        if node_data is None:
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

        return retTmpDict

    @transact
    def get_admin_info(self):

        check_single_entry();

        store = self.getStore()

        # this unmaintainable crap need to be removed in the future,
        # and the dict/output generation shall not be scattered
        # around here.
        retAdminDict= { 'name' : unicode(node_data.name),
                        'description' : unicode(node_data.description),
                        'hidden_service' : unicode(node_data.hidden_service),
                        'public_site' : unicode(node_data.public_site),
                        'public_stats_update_time' : unicode(node_data.public_stats_update_time),
                        'private_stats_update_time' : unicode(node_data.private_stats_update_time),
                        'email' : unicode(node_data.email),
                        'languages' : unicode(node_data.languages)
            }

        return retAdminDict
