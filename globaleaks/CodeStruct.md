## Code Structure

In this file, are reported the files below the tree of globaleaks/, keeping track of the 
functions and classess exported

globaleaks/

    __init__.py
    backend.py
    task.py
        TaskQueue
        DummyMethod
        Task

    node.py (Processor)
        Node
    admin.py (Processor)
        Admin
    tip.py (Processor)
        Tip

globaleaks/receiver/

    __init__.py (I don't get it, why in __init__ ?)

globaleaks/rest/

    api.py
        specify API name and handle the REST paths
        import twisted

    handlers.py
        XXX in future will be splitted,
        contains function called by REST

    utils.py
        utilities used by api and handlers,

globaleaks/utils/

    random.py
        random_string

    log.py
        Logging

globaleaks/modules/

    contains abstract Factories and their implementation:

    notify/
    delivery/

    not yet written:
        diskstorage/
        databasestorage/
        tip/
        receivers/
        inputfilter/


globaleaks/utils/

    random.py
    JSONhelper.py
