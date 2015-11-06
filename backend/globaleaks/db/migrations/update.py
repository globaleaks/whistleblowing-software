# -*- encoding: utf-8 -*-
import os

from twisted.python import log
from storm.exceptions import OperationalError
from storm.locals import create_database, Store
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
    def __init__(self, table_history, start_version, store_old, store_new):
        self.appdata = load_appdata()

        self.table_history = table_history
        self.start_version = start_version

        self.store_old = store_old
        self.store_new = store_new

        self.model_from = {}
        self.model_to = {}
        self.entries_count = {}
        self.fail_on_count_mismatch = {}

        self.std_fancy = " ł "
        self.debug_info = "   [%d => %d] " % (start_version, start_version + 1)

        for model_name, model_history in table_history.iteritems():
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
            log.msg('{} Acquire SQL schema {}'.format(self.debug_info, GLSettings.db_schema_file))

            if not os.access(GLSettings.db_schema_file, os.R_OK):
                log.msg('Unable to access', GLSettings.db_schema_file)
                raise IOError('Unable to access db schema file')
            with open(GLSettings.db_schema_file) as f:
                create_queries = ''.join(f).split(';')
                for create_query in create_queries:
                    try:
                        self.store_new.execute(create_query + ';')
                    except OperationalError:
                        log.msg('OperationalError in "{}"'.format(create_query))
                        raise excep

        else: # manage the migrantion here
            for k, _ in self.table_history.iteritems():
                create_query = self.get_right_sql_version(k, self.start_version + 1)
                if not create_query:
                    # the table has been removed
                    continue

                try:
                    self.store_new.execute(create_query + ';')
                except OperationalError as excep:
                    log.msg('{} OperationalError in [{}]'.format(self.debug_info, create_query))
                    raise excep

        self.store_new.commit()

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

        if model_name not in self.table_history:
            msg = 'Not implemented usage of get_right_model {} ({} {})'.format(
                __file__, model_name, self.start_version)
            raise NotImplementedError(msg)

        if version > DATABASE_VERSION:
            raise ValueError('Version supplied must be less or equal to {}'.format(
                DATABASE_VERSION))

        if self.table_history[model_name][table_index] == -1:
            return None

        while table_index >= 0:
            if self.table_history[model_name][table_index] != 0:
                return self.table_history[model_name][table_index]
            table_index -= 1

        return None

    def get_right_sql_version(self, model_name, version):
        """
        @param model_name:
        @param version:
        @return:
            The SQL right for the stuff we've
        """
        model_obj = self.get_right_model(model_name, version)
        if model_obj is None:
            return None

        return generateCreateQuery(model_obj)

    def _perform_copy_list(self, model_name):
        objs_count = self.store_old.find(self.model_from[model_name]).count()

        log.msg('{} default {} migration assistant: #{}'.format(
            self.debug_info, model_name, objs_count))

        old_objects = self.store_old.find(self.model_from[model_name])

        for old_obj in old_objects:
            new_obj = self.model_to[model_name]()

            # Storm internals simply reversed
            for _, v in new_obj._storm_columns.iteritems():
                old_value = getattr(old_obj, v.name)
                if old_value is not None:
                    setattr(new_obj, v.name, old_value)

            self.store_new.add(new_obj)

    def _perform_copy_single(self, model_name):
        log.msg('{} default {} migration assistant'.format(self.debug_info, model_name))

        old_obj = self.store_old.find(self.model_from[model_name]).one()
        new_obj = self.model_to[model_name]()

        # Storm internals simply reversed
        for _, v in new_obj._storm_columns.iteritems():
            old_value = getattr(old_obj, v.name)
            if old_value is not None:
                setattr(new_obj, v.name, old_value)

        self.store_new.add(new_obj)

    def update_model_with_new_templates(self, model_obj, var_name, templates_list, templates_dict):
        if var_name in templates_list:
            # check needed to preserve funtionality if templates will be altered in the future
            if var_name in templates_dict:
                template_text = templates_dict[var_name]
            else:
                template_text = every_language("")

            setattr(model_obj, var_name, template_text)
            return True

        return False

    def migrate_ApplicationData(self):
        return

    def migrate_Context(self):
        self._perform_copy_list("Context")

    def migrate_Node(self):
        self._perform_copy_single("Node")

    def migrate_User(self):
        self._perform_copy_list("User")

    def migrate_ReceiverTip(self):
        self._perform_copy_list("ReceiverTip")

    def migrate_WhistleblowerTip(self):
        self._perform_copy_list("WhistleblowerTip")

    def migrate_Comment(self):
        self._perform_copy_list("Comment")

    def migrate_InternalTip(self):
        self._perform_copy_list("InternalTip")

    def migrate_Receiver(self):
        self._perform_copy_list("Receiver")

    def migrate_InternalFile(self):
        self._perform_copy_list("InternalFile")

    def migrate_ReceiverFile(self):
        self._perform_copy_list("ReceiverFile")

    def migrate_Notification(self):
        self._perform_copy_single("Notification")

    def migrate_ReceiverContext(self):
        self._perform_copy_list("ReceiverContext")

    def migrate_ReceiverInternalTip(self):
        self._perform_copy_list("ReceiverInternalTip")

    def migrate_Message(self):
        self._perform_copy_list("Message")

    def migrate_Stats(self):
        self._perform_copy_list("Stats")

    def migrate_Field(self):
        self._perform_copy_list("Field")

    def migrate_FieldAttr(self):
        self._perform_copy_list("FieldAttr")

    def migrate_FieldOption(self):
        self._perform_copy_list("FieldOption")

    def migrate_OptionActivateField(self):
        self._perform_copy_list("OptionActivateField")

    def migrate_OptionActivateStep(self):
        self._perform_copy_list("OptionActivateStep")

    def migrate_FieldField(self):
        self._perform_copy_list("FieldField")

    def migrate_Step(self):
        self._perform_copy_list("Step")

    def migrate_StepField(self):
        self._perform_copy_list("StepField")

    def migrate_Anomalies(self):
        self._perform_copy_list("Anomalies")

    def migrate_EventLogs(self):
        self._perform_copy_list("EventLogs")

    def migrate_FieldAnswer(self):
        self._perform_copy_list("FieldAnswer")

    def migrate_FieldAnswerGroup(self):
        self._perform_copy_list("FieldAnswerGroup")

    def migrate_FieldAnswerGroupFieldAnswer(self):
        self._perform_copy_list("FieldAnswerGroupFieldAnswer")

    def migrate_ArchivedSchema(self):
        self._perform_copy_list("ArchivedSchema")
