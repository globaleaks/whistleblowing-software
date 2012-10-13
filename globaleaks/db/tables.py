from twisted.internet.defer import inlineCallbacks

from storm.locals import *
from storm.properties import PropertyColumn
from storm.variables import *

def variableToSQLite(var_type):
    sqlite_type = "VARCHAR"
    if isinstance(var_type, BoolVariable):
        sqlite_type = "INTEGER"
    elif isinstance(var_type, DateTimeVariable):
        pass
        sqlite_type = ""
    elif isinstance(var_type, DateVariable):
        pass
    elif isinstance(var_type, DecimalVariable):
        pass
    elif isinstance(var_type, EnumVariable):
        sqlite_type = "BLOB"
    elif isinstance(var_type, FloatVariable):
        sqlite_type = "REAL"
    elif isinstance(var_type, IntVariable):
        sqlite_type = "INTEGER"
    elif isinstance(var_type, RawStrVariable):
        sqlite_type = "BLOB"
    elif isinstance(var_type, TimeDeltaVariable):
        pass
    elif isinstance(var_type, TimeVariable):
        pass
    elif isinstance(var_type, UUIDVariable):
        pass
    elif isinstance(var_type, UnicodeVariable):
        pass
    elif isinstance(var_type, JSONVariable):
        sqlite_type = "BLOB"
    elif isinstance(var_type, PickleVariable):
        sqlite_type = "BLOB"
    return "%s" % sqlite_type

def varsToParametersSQLite(variables, primary_keys):
    params = "("
    for var in variables[:-1]:
        params += "%s %s, " % var
    if len(primary_keys) > 0:
        params += "%s %s, " % variables[-1]
        params += "PRIMARY KEY ("
        for key in primary_keys[:-1]:
            params += "%s, " % key
        params += "%s))" % primary_keys[-1]
    else:
        params += "%s %s)" % variables[-1]
    return params

def generateCreateQuery(model):
    query = "CREATE TABLE "+ model.__storm_table__ + " "

    variables = []
    primary_keys = []

    for attr in dir(model):
        a = getattr(model, attr)
        if isinstance(a, PropertyColumn):
            var_stype = a.variable_factory()
            var_type = variableToSQLite(var_stype)
            name = a.name
            variables.append((name, var_type))
            if a.primary:
                primary_keys.append(name)

    query += varsToParametersSQLite(variables, primary_keys)
    return query

def createTable(model, transactor, database):
    if not transactor:
        from globaleaks.db import transactor
    if not database:
        from globaleaks.db import database
    store = Store(database)
    createQuery = generateCreateQuery(model)
    try:
        store.execute(createQuery)
    except Exception, e:
        print "Failed to create table!"
        print e
        store.close()
    store.commit()
    store.close()

@inlineCallbacks
def runCreateTable(model, transactor=None, database=None):
    yield transactor.run(createTable, model, transactor, database)

