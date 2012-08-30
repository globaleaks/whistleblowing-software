from storm.twisted.transact import transact
from storm.locals import *

__all__ = ['InternalTip', 'MaterialSet',
           'StoredFile', 'Tip','ReceiverTip',
           'WhistleblowerTip', 'Node', 'Receiver']

class TXModel(object):
    """
    This is the model to be subclassed for having the DB operations be done on
    storm ORM.

    The methods that should be run on the Storm ORM should be decorated with
    @transact. Be sure *not* to return any reference to Storm objects, these
    where retrieved in a different thread and cannot exit the matrix.
    """
    create_query = ""
    def __init__(self):
        from globaleaks.db import transactor, database
        self.transactor = transactor
        self.database = database

    def _create_store(self):
        self.store = Store(self.database)

    @transact
    def create_table(self):
        self._create_store()
        try:
            self.store.execute(self.create_query)
        except:
            pass
        self.store.commit()

    @transact
    def store(self):
        self._create_store()
        self.store.add(self)
        self.store.commit()

class StoredFile(TXModel):
    """
    Represents a material: a file.
    """
    __storm_table__ = 'material'

    create_query = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, file_location VARCHAR, description VARCHAR, "\
                   " materialset_id INTEGER)"

    id = Int(primary=True)

    file_location = Unicode()
    description = Unicode()

    materialset_id = Int()

    #materialset = Reference(materialset_id, MaterialSet.id)

class MaterialSet(TXModel):
    """
    This represents a material set: a collection of files.
    """
    __storm_table__ = 'materialset'

    create_query = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, description VARCHAR, "\
                   " internaltip_id INTEGER)"

    id = Int(primary=True)
    description = Unicode()

    internaltip_id = Int()

    #tip = Reference(internaltip_id, InternalTip.id)
    files = ReferenceSet(id, StoredFile.materialset_id)

class InternalTip(TXModel):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.
    It has a one-to-many association with the individual Tips of every receiver
    and whistleblower.
    """
    __storm_table__ = 'internaltip'

    create_query = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, fields VARCHAR, comments VARCHAR,"\
                   " pertinence INTEGER, expiration_time VARCHAR, material_id INT)"

    id = Int(primary=True)

    fields = Pickle()
    comments = Pickle()
    pertinence = Int()
    expiration_time = Date()

    material_id = Int()

    # Material sets associated with the submission
    material = ReferenceSet(id, MaterialSet.internaltip_id)
    # Tips associated with this InternalTip
    # children = ReferenceSet(id, Tip.internaltip_id)

    def __repr__(self):
        return "<InternalTip: (%s, %s, %s, %s, %s)" % (self.fields, \
                self.material, self.comments, self.pertinence, \
                self.expiration_time)

class Tip(TXModel):
    __storm_table__ = 'tip'

    create_query = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, address VARCHAR, password VARCHAR,"\
                   " type INTEGER, internaltip_id INTEGER, total_view_count INTEGER, "\
                   " total_download_count INTEGER, relative_view_count INTEGER, "\
                   " relative_download_count INTEGER)"

    id = Int(primary=True)

    type = Int()
    address = Unicode()
    password = Unicode()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    def get_type(self):
        if self.__class__ is ReceiverTip:
            return 0
        elif self.__class__ is WhistleblowerTip:
            return 1
        elif self.__class is Tip:
            return 9

    def gen_address(self):
        # XXX DANGER CHANGE!!
        self.address = sha.sha(''.join(str(random.randint(1,100)) for x in range(1,10))).hexdigest()
        self.password = ""

    def add_comment(self, data):
        pass

class ReceiverTip(Tip):
    total_view_count = Int()
    total_download_count = Int()
    relative_view_count = Int()
    relative_download_count = Int()

    def increment_visit(self):
        pass

    def increment_download(self):
        pass

    def delete_tulip(self):
        pass

    def download_material(self, id):
        pass

class WhistleblowerTip(Tip):

    def add_material(self):
        pass


class Node(TXModel):
    __storm_table__ = 'node'

    id = Int(primary=True)

    context = Pickle()
    statistics = Pickle()
    properties = Pickle()
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()

class Receiver(TXModel):
    __storm_table = 'receivers'

    public_name = Unicode()
    private_name = Unicode()


