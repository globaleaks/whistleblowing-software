## Models recurring pattern

    class ModelName(TXModel):

TXmodel is implemented in globaleaks/models/base.py 


    @transact
    get_all()
    
    @transact
    get_single()

Every model has almost two method to extract information about the content, get\_single expect
the primary key of the database entry, and get\_all just return all the available elements in
the associated table.

Every method marked with decorator **transact** are executd in a separated thread, handled by
Storm ORM, Storm ORM provide rollback whenever an exception is raised, and commit when the 
function is completed.

    _description_dict()

This is the method, without decorator (because called by other @transact methods) that perform 
serialization. It do not have to contain reference of transact thread (In example: no
self.something, but the copy of that, like unicode(self.something) )

    _import_dict()

When a resource need to be updated, a support function just take the input dictionary and copy
them into the database. The input has been already validate by the validateMessage function,
in the handler.
