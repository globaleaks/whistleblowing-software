## Code Structure

In the file, we can specify the Threaded logic, this shall be helpful, twisted and
sqlalchemy has not to run in the same thread.

/

    __init__.py
    backend.py (main!)

core/

    ORM (TODO)
    task
    submission

rest/

    api.py
        specify API name and handle the REST paths
        import twisted

    handlers.py
        XXX in future will be splitted,
        contains function called by REST

    utils.py
        utilities used by api and handlers,

modules/

    contains abstract Factories and their implementation:


    diskstorage/
    databasestorage/
    notification/
    delivery/
    tip/
    receivers/
    inputfilter/


utils/

    random.py
    JSONhelper.py
