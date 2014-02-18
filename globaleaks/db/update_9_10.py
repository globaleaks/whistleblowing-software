# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

class ApplicationData_version_10(Model):
    __storm_table__ = 'applicationdata'
    fields_version = Int()
    fields = Pickle()


class Node_version_9(Model):
    __storm_table__ = 'node'

    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    languages_enabled = Pickle()
    default_language = Unicode()
    description = Pickle()
    presentation = Pickle()
    footer = Pickle()
    subtitle = Pickle()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    exception_email = Unicode()

    # is added
    # wizard_done = Bool()
    # anomaly_checks = Bool()

class Receiver_version_9(Model):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = Pickle()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    receiver_level = Int()
    last_update = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()
    presentation_order = Int()
    # this gpg_enable_files is removed since 9 to 10
    gpg_enable_files = Bool()

class User_version_9(Model):
    __storm_table__ = 'user'
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    # this failed_login_count is removed since 9 to 10
    failed_login_count = Int()


class Replacer910(TableReplacer):


    def migrate_Node(self):
        print "%s Node migration assistant: (privileges, subtitle)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 9)).one()
        new_node = self.get_right_model("Node", 10)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'wizard_done':
                new_node.wizard_done = True
                continue

            if v.name == 'anomaly_checks':
                anomaly_checks = True
                continue

            setattr(new_node, v.name, getattr(old_node, v.name) )

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_InternalFile(self):
        """
        The following is the same comment present in migration 8->9 as the bug still
        exist because InternalFile.description was not initialized in InternalFile creation
        in file.py handler.

        The integration of 'description' happen between the v 7 and 8, but
        InternalFile.description has been set with storm validator after the
        release.

        This mean that old DB can't be converted anymore because description was
        accepted empty (at the moment, from the GLC UI, can't be set a file desc)

        This migrate_InternalFile do not require an update of the version table:
        self.get_right_model("InternalFile", 8)
        and
        self.get_right_model("InternalFile", 9)
        return the same object, and is fine so.
        """
        print "%s InternalFile migration assistant: (file description is mandatory !?) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("InternalFile", 8)).count() )

        old_ifiles = self.store_old.find(self.get_right_model("InternalFile", 8))

        for old_obj in old_ifiles:

            new_obj = self.get_right_model("InternalFile", 9)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'description':
                    if not old_obj.description or not len(old_obj.description):
                        new_obj.description = "Descriptionless %s file" % old_obj.content_type
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
        self.store_new.commit()

    def epilogue(self):
        print "%s Epilogue function in migration assistant: (stats, appdata)" % \
              self.std_fancy

        # first stats is not generated here, do not need
        appdata = ApplicationData_version_10()
        appdata.fields_version = 0
        appdata.fields = None

        self.store_new.add(appdata)
        self.store_new.commit()

