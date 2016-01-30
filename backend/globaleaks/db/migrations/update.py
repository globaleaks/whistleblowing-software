# -*- encoding: utf-8 -*-
import os

from storm.exceptions import OperationalError
from storm.properties import PropertyColumn
from storm.variables import BoolVariable, DateTimeVariable
from storm.variables import EnumVariable, IntVariable, RawStrVariable, PickleVariable
from storm.variables import UnicodeVariable, JSONVariable

from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db.appdata import load_appdata
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import every_language


def variableToSQL(var, db_type):
    """
    We take as input a storm.variable and we output the SQLite string it
    represents.
    """
    if isinstance(var, BoolVariable):
        data_mapping = {
            "sqlite": "INTEGER",
        }
    elif isinstance(var, DateTimeVariable):
        data_mapping = {
            "sqlite": "VARCHAR",
        }
    elif isinstance(var, EnumVariable):
        data_mapping = {
            "sqlite": "BLOB",
        }
    elif isinstance(var, IntVariable):
        data_mapping = {
            "sqlite": "INTEGER",
        }
    elif isinstance(var, RawStrVariable):
        data_mapping = {
            "sqlite": "BLOB",
        }
    elif isinstance(var, UnicodeVariable):
        data_mapping = {
            "sqlite": "VARCHAR",
        }
    elif isinstance(var, JSONVariable):
        data_mapping = {
            "sqlite": "BLOB",
        }
    elif isinstance(var, PickleVariable):
        data_mapping = {
            "sqlite": "BLOB",
        }
    else:
        raise ValueError('Invalid var: {}'.format(var))

    return "%s" % data_mapping[db_type]


def varsToParametersSQL(variables, primary_keys, db_type):
    """
    Takes as input a list of variables (convered to SQLite syntax and in the
    form of strings) and primary_keys.
    Outputs these variables converted into paramter syntax for SQLites.

    ex.
        variables: ["var1 INTEGER", "var2 BOOL", "var3 INTEGER"]
        primary_keys: ["var1"]

        output: "(var1 INTEGER, var2 BOOL, var3 INTEGER PRIMARY KEY (var1))"
    """
    params = "("
    for var in variables[:-1]:
        params += "%s %s, " % (var[0], var[1])
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
    """
    This takes as input a Storm model and outputs the creation query for it.
    """
    prehistory = model.__storm_table__.find("_v_")
    if prehistory != -1:
        model_name = model.__storm_table__[:prehistory]
    else:
        model_name = model.__storm_table__

    query = "CREATE TABLE " + model_name + " "

    variables = []
    primary_keys = []

    for attr in dir(model):
        a = getattr(model, attr)
        if isinstance(a, PropertyColumn):
            var = a.variable_factory()
            data_mapping = variableToSQL(var, GLSettings.db_type)
            name = a.name
            variables.append((name, data_mapping))
            if a.primary:
                primary_keys.append(name)

    query += varsToParametersSQL(variables, primary_keys, GLSettings.db_type)

    return query


class MigrationBase(object):
    """
    This is the base class used by every Updater
    """
    def __init__(self, migration_mapping, start_version, store_old, store_new):
        self.appdata = load_appdata()

        self.migration_mapping = migration_mapping
        self.start_version = start_version

        self.store_old = store_old
        self.store_new = store_new

        self.model_from = {}
        self.model_to = {}
        self.entries_count = {}
        self.fail_on_count_mismatch = {}

        for model_name, model_history in migration_mapping.iteritems():
            length = DATABASE_VERSION + 1 - FIRST_DATABASE_VERSION_SUPPORTED
            if len(model_history) != length:
                raise TypeError('Expecting a table with {} statuses ({})'.format(length, model_name))

            self.fail_on_count_mismatch[model_name] = True

            self.model_from[model_name] = self.get_right_model(model_name, start_version)
            self.model_to[model_name] = self.get_right_model(model_name, start_version + 1)

            if self.model_from[model_name] is not None and self.model_to[model_name] is not None:
                self.entries_count[model_name] = self.store_old.find(self.model_from[model_name]).count()
            else:
                self.entries_count[model_name] = 0

        if self.start_version + 1 == DATABASE_VERSION:
            # we are there!
            if not os.access(GLSettings.db_schema, os.R_OK):
                GLSettings.print_msg("Unable to access %s ' % GLSettings.db_schema")
                raise IOError('Unable to access db schema file')
            with open(GLSettings.db_schema) as f:
                queries = ''.join(f).split(';')
                for query in queries:
                    self.execute_query(query)

        else: # manage the migrantion here
            for k, _ in self.migration_mapping.iteritems():
                query = self.get_right_sql_version(k, self.start_version + 1)
                if not query:
                    # the table has been removed
                    continue

                self.execute_query(query)

        self.store_new.commit()

    def execute_query(self, query):
        try:
            self.store_new.execute(query + ';')
        except OperationalError as excep:
            GLSetting.print_msg('OperationalError %s while executing query: %s' % (excep, query))
            raise excep

    def commit(self):
        self.store_new.commit()

    def close(self):
        self.store_old.close()
        self.store_new.close()

    def prologue(self):
        pass

    def epilogue(self):
        pass

    def get_right_model(self, model_name, version):
        table_index = (version - FIRST_DATABASE_VERSION_SUPPORTED)

        if model_name not in self.migration_mapping:
            msg = 'Not implemented usage of get_right_model {} ({} {})'.format(
                __file__, model_name, self.start_version)
            raise NotImplementedError(msg)

        if version > DATABASE_VERSION:
            raise ValueError('Version supplied must be less or equal to {}'.format(
                DATABASE_VERSION))

        if self.migration_mapping[model_name][table_index] == -1:
            return None

        while table_index >= 0:
            if self.migration_mapping[model_name][table_index] != 0:
                return self.migration_mapping[model_name][table_index]
            table_index -= 1

        return None

    def get_right_sql_version(self, model_name, version):
        model_obj = self.get_right_model(model_name, version)
        if model_obj is None:
            return None

        return generateCreateQuery(model_obj)

    def update_model_with_new_templates(self, model_obj, var_name, template_list, templates_dict):
        if var_name in template_list:
            # check needed to preserve funtionality if templates will be altered in the future
            if var_name in templates_dict:
                template_text = templates_dict[var_name]
            else:
                template_text = every_language("")

            setattr(model_obj, var_name, template_text)
            return True

        return False

    def generic_migration_function(self, model_name):
        old_objects = self.store_old.find(self.model_from[model_name])

        for old_obj in old_objects:
            new_obj = self.model_to[model_name]()

            # Storm internals simply reversed
            for _, v in new_obj._storm_columns.iteritems():
                old_value = getattr(old_obj, v.name)
                if old_value is not None:
                    setattr(new_obj, v.name, old_value)

            self.store_new.add(new_obj)

    def migrate_model(self, model_name):
        objs_count = self.store_old.find(self.model_from[model_name]).count()

        specific_migration_function = getattr(self, 'migrate_%s' % model_name, None)
        if specific_migration_function is not None:
            GLSettings.print_msg(' ł %s [#%d]' % (model_name, objs_count))
            specific_migration_function()
        else:
            GLSettings.print_msg(' * %s [#%d]' % (model_name, objs_count))
            self.generic_migration_function(model_name)
