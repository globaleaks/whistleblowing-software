## Models recurring pattern

    class ModelName(TXModel):

TXmodel is implemented in globaleaks/models/base.py 


    get_all()
    get_single()

Every model has almost two method to extract information about the content, get\_single expect
the primary key of the database entry, and get\_all just return all the available elements in
the associated table.

Every method marked with decorator **transact** are executd in a separated thread, handled by
Storm ORM, Storm ORM provide rollback whenever an exception is raised, and commit when the 
function is completed.


    new(received_dict)

Mostly of the models had a funcion called new, it's used when a new instance of the object
had to be created. A new() function return always the instance initialized as serialized by
\_desription\_dict function, explained below. new instance initialize the object self and 
then add them to the store. new can raise InvalidInputFormat exception, and depending on
the model, other specific exception.. *Commonly* is called after a POST HTTP event.


    update(id, received_dict)

Mostly of the models implement a function called update, its take the primary key able to 
identify an existing instance. The istance is then opened and updated in the fields that
may be updated. *Commonly* is called by a PUT event. This function can raise
InvalidInputFormat, error in found the primary key requested, and depending on the specific
model, other specific exception.


    _description_dict()

This is the method, without decorator (because called by other @transact methods) that perform 
serialization. It do not have to contain reference of transact thread (In example: no
self.something, but the copy of that, like unicode(self.something) )

    _import_dict()

When a resource need to be updated, a support function just take the input dictionary and copy
them into the database. The input has been already validate by the validateMessage function,
in the handler, anyway this function can raise a couple of exception (KeyError, because works 
with dictionary, and TypeError, because Storm variables can be type-validated), and those
exception are catch in the called (new and update).

