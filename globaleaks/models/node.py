# -*- coding: UTF-8
#
#   models/node
#   ***********
#
# Manage the single table containing all the node general information,
# can be accessed with different privileges (admin and unprivileged).

from storm.exceptions import NotOneError
from storm.store import AutoReload
from storm.locals import Int, Pickle, Unicode, DateTime

from globaleaks.models.base import TXModel
from globaleaks.utils import log
from globaleaks.rest.errors import NodeNotFound, InvalidInputFormat

__all__ = [ 'Node' ]

class Node(TXModel):

    def new(self, input_dict):

        node_list = self.store.find(Node)

        if node_list.count() != 0:
            raise NotImplementedError("Node already created!")

        try:
            self._import_dict(input_dict)
        except KeyError, e:
            raise InvalidInputFormat("Node initialization fail (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Node initialization fail (wrong %s)" % e)

        self.store.add(self)
        return self._description_dict()

    def update(self, input_dict):
        """
        @param input_dict: input dictionary
        @return: None
        """

        try:
            node_data = self.store.find(Node, 1 == Node.id).one()
        except NotOneError:
            raise NodeNotFound
        if node_data is None:
            raise NodeNotFound

        try:
            node_data._import_dict(input_dict)

            # those elements are present only in update
            node_data.notification_settings = input_dict['notification_settings']
            node_data.password = input_dict['password']

        except KeyError, e:
            raise InvalidInputFormat("Node update fail (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Node update fail (wrong %s)" % e)

        log.msg("Updated node main configuration")

        return node_data._description_dict()

    def get_single(self):

        node_list = self.store.find(Node)

        if node_list.count() != 1:
            raise NotImplementedError("Unexpected condition: More than one Node configured (%d)" % node_list.count())

        return node_list[0]._description_dict()

    def _import_dict(self, input_dict):

        self.description = input_dict['description']
        self.name = input_dict['name']
        self.public_site = input_dict['public_site']
        self.hidden_service = input_dict['hidden_service']
        self.email = input_dict['email']
        self.languages = input_dict['languages']
        self.stats_update_time = int(input_dict['stats_update_time'])
        self.password = input_dict['password']

    def _description_dict(self):

        retDict= { 'name' : unicode(self.name),
                   'description' : unicode(self.description),
                   'hidden_service' : unicode(self.hidden_service),
                   'public_site' : unicode(self.public_site),
                   'stats_update_time' : int(self.stats_update_time),
                   'email' : unicode(self.email),
                   'notification_settings' : dict(self.notification_settings) if self.notification_settings else None,
                   'password' : unicode(self.password),
                   'languages' : list(self.languages)
            }
        return retDict
