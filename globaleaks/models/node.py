from storm.twisted.transact import transact

from storm.locals import Int, Pickle, Date
from storm.locals import Unicode, Bool, DateTime
from storm.locals import ReferenceSet

from globaleaks.models.base import TXModel
from globaleaks.models.admin import Context
from globaleaks.utils import log


"""
Manage the single table containings all the node general information,
can be accessed with different privileges (admin and unprivileged).
"""

class Node(TXModel):
    """
    This table has only one instance, has the "id", but would not exists a second element
    of this table. This table act, more or less, like the configuration file of the previous
    GlobaLeaks release (and some of the GL 0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class SystemSettings")
    __storm_table__ = 'systemsettings'

    id = Int(primary=True)

    statistics = Pickle()
    properties = Pickle()
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()

    creation_time = DateTime()
    url_schema = Unicode()

    private_stats_delta = Int()
    public_stata_delta = Int()

    """
    XXX To be implemented with APAF,
    public_key,
    XXX to be partially specified:
    leakdirectory_entry
    XXX missing: languages
    """

    @transact
    def configure_node(self):
        pass

    @transact
    def get_public_info(self):
        pass

    @transact
    def list_contexts(self):
        pass

Node.contexts = ReferenceSet(Node.id, Context.node_id)


