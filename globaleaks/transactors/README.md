# What's in this directory

Implementation of the **macro operations** between REST API and database interacation.

# Technical details

Storm database require a separated thread to run. This thread is executed when a function
is decorated with **@transact**

If an exception is raised inside this transact, a database rollback is performed deleting
all the operations performed in the store.

store is the database handler, and on top of every macro operation contained in this
directory, a new store is created and passed to the models (models/ directory, containing
the description of the ORM)

# Files in this directory

## CrudOperations

### Pattern

The recurring operations from the REST API are described in rest/api.py, and basically 
are five:

  * listing of a resource collection
  * creation of a new resource
  * retrival of a resource
  * update of a resource
  * deletion of a resource

And therefore, the method in CrudOperation class are:

  * get\_\*\_list (context, receiver, plugin, tip, profiles)
  * create\_\*
  * get\_\*
  * update\_\*
  * delete\_\*

## asyncoperation



