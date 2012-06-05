## Code Structure

In the file, we can specify the Threaded logic, this shall be helpful, twisted and
sqlalchemy has not to run in the same thread.

/

    __init__.py

storage/

    since storage class depends db functions, and manage
    the saving, encryption, distribution of the files

db/

    db directory contains the following files:

    receiver.py
    tip.py
    filestorage.py
 
    DBIO.py
        support declaration of the object under modification,
        aggregate commit functions, supports DB-objects sync
        dump, resume operations

rest/

    api.py
        specify API name and handle the REST paths
        import twisted

    handlers.py
        in future will be splitted,
        contains function called by REST

    utils.py

    accessauth.py
        to be implemented, contain authentication function
        for Receivers and WB 

notify/



delivery/
