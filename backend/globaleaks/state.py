# -*- coding: utf-8
import os
import sys

from twisted.internet import defer
from twisted.python.threadpool import ThreadPool

from globaleaks import __version__, orm, models
from globaleaks.utils.agent import get_tor_agent, get_web_agent
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.templating import Templating
from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.security import sha256
from globaleaks.utils.utility import datetime_now, log
from globaleaks.utils.tempdict import TempDict

def getAlarm(state):
    from globaleaks.anomaly import Alarm
    return Alarm(state)


class TenantState(object):
    def __init__(self, state):
        self.RecentEventQ = []
        self.EventQ = []
        self.AnomaliesQ = []

        # An ACME challenge will have 5 minutes to resolve
        self.acme_tmp_chall_dict = TempDict(300)

        self.Alarm = getAlarm(state)


class StateClass(ObjectDict):
    __metaclass__ = Singleton

    def __init__(self):
        from globaleaks.settings import Settings

        self.settings = Settings

        self.process_supervisor = None
        self.tor_exit_set = TorExitSet()

        self.https_socks = []
        self.http_socks = []
        self.jobs = []
        self.jobs_monitor = None
        self.services = []

        self.api_token_session = None

        self.exceptions = {}
        self.exceptions_email_count = 0
        self.mail_counters = {}
        self.stats_collection_start_time = datetime_now()

        self.accept_submissions = True

        self.tenant_state = {}
        self.tenant_cache = {}
        self.tenant_hostname_id_map = {}

        self.set_orm_tp(ThreadPool(4, 16))
        self.TempUploadFiles = TempDict(timeout=3600)

    def init_environment(self):
        os.umask(077)
        self.settings.eval_paths()
        self.create_directories()
        self.cleaning_dead_files()

    def set_orm_tp(self, orm_tp):
        self.orm_tp = orm_tp
        orm.set_thread_pool(orm_tp)

    def get_agent(self, tid=1):
        if self.tenant_cache[tid].anonymize_outgoing_connections:
            return get_tor_agent(self.settings.socks_host, self.settings.socks_port)

        return get_web_agent()

    def create_directory(self, path):
        """
        Create the specified directory;
        Returns True on success, False if the directory was already existing
        """
        if os.path.exists(path):
            return False

        log.debug("Creating directory: %s", path)

        try:
            os.mkdir(path)
        except OSError as excep:
            log.debug("Error in creating directory: %s (%s)", path, excep.strerror)
            raise excep

        return True

    def create_directories(self):
        """
        Execute some consistency checks on command provided Globaleaks paths

        if one of working_path or static path is created we copy
        here the static files (default logs, and in the future pot files for localization)
        because here stay all the files needed by the application except the python scripts
        """
        for dirpath in [self.settings.working_path,
                        self.settings.db_path,
                        self.settings.files_path,
                        self.settings.attachments_path,
                        self.settings.tmp_path,
                        self.settings.log_path,
                        self.settings.backups_path]:
            self.create_directory(dirpath)

    def cleaning_dead_files(self):
        """
        This function is called at the start of GlobaLeaks, in
        bin/globaleaks, and checks if the file is present in
        temporally_encrypted_dir
        """
        # temporary .aes files must be simply deleted
        for f in os.listdir(self.settings.tmp_path):
            path = os.path.join(self.settings.tmp_path, f)
            log.debug("Removing old temporary file: %s", path)

            try:
                os.remove(path)
            except OSError as excep:
                log.debug("Error while evaluating removal for %s: %s", path, excep.strerror)

        # temporary .aes files with lost keys can be deleted
        # while temporary .aes files with valid current key
        # will be automagically handled by delivery sched.
        keypath = os.path.join(self.settings.tmp_path, self.settings.AES_keyfile_prefix)

        for f in os.listdir(self.settings.attachments_path):
            path = os.path.join(self.settings.attachments_path, f)
            try:
                result = self.settings.AES_file_regexp_comp.match(f)
                if result is not None:
                    if not os.path.isfile("%s%s" % (keypath, result.group(1))):
                        log.debug("Removing old encrypted file (lost key): %s", path)
                        os.remove(path)
            except Exception as excep:
                log.debug("Error while evaluating removal for %s: %s", path, excep)

    def get_mail_counter(self, receiver_id):
        return self.mail_counters.get(receiver_id, 0)

    def increment_mail_counter(self, receiver_id):
        self.mail_counters[receiver_id] = self.mail_counters.get(receiver_id, 0) + 1

    def reset_hourly(self):
        for tid in self.tenant_state:
            self.tenant_state[tid] = TenantState(self)

        self.exceptions.clear()
        self.exceptions_email_count = 0
        self.mail_counters.clear()

        self.stats_collection_start_time = datetime_now()

    def sendmail(self, tid, to_address, subject, body):
       if self.settings.testing:
           # during unit testing do not try to send the mail
           return defer.succeed(True)

       return sendmail(tid,
                       self.tenant_cache[tid].notification.smtp_username,
                       self.tenant_cache[tid].notification.smtp_password,
                       self.tenant_cache[tid].notification.smtp_server,
                       self.tenant_cache[tid].notification.smtp_port,
                       self.tenant_cache[tid].notification.smtp_security,
                       self.tenant_cache[tid].notification.smtp_source_name,
                       self.tenant_cache[tid].notification.smtp_source_email,
                       to_address,
                       subject,
                       body,
                       self.tenant_cache[tid].anonymize_outgoing_connections,
                       self.settings.socks_host,
                       self.settings.socks_port)


    def schedule_exception_email(self, exception_text, *args):
        from globaleaks.transactions import schedule_email

        if not hasattr(self.tenant_cache[1], 'notification'):
            log.err("Error: Cannot send mail exception before complete initialization.")
            return

        if self.exceptions_email_count >= self.settings.exceptions_email_hourly_limit:
            return

        exception_text = (exception_text % args) if args else exception_text

        sha256_hash = sha256(bytes(exception_text))

        if sha256_hash not in self.exceptions:
            self.exceptions[sha256_hash] = 0

        self.exceptions[sha256_hash] += 1
        if self.exceptions[sha256_hash] > 5:
            log.err("Exception mail suppressed for (%s) [reason: threshold exceeded]",  sha256_hash)
            return

        self.exceptions_email_count += 1

        mail_subject = "GlobaLeaks Exception"
        delivery_list = self.tenant_cache[1].notification.exception_delivery_list

        if self.settings.devel_mode:
            mail_subject +=  " [%s]" % self.settings.developer_name
            delivery_list = [("globaleaks-stackexception-devel@globaleaks.org", '')]

        mail_body = bytes("Platform: %s (%s)\nVersion: %s\n\n%s" \
                          % (self.tenant_cache[1].hostname,
                             self.tenant_cache[1].onionservice,
                             __version__,
                             exception_text))

        for mail_address, pgp_key_public in delivery_list:
            # Opportunisticly encrypt the mail body. NOTE that mails will go out
            # unencrypted if one address in the list does not have a public key set.
            if pgp_key_public:
               pgpctx = PGPContext(self.settings.tmp_path)
               fingerprint = pgpctx.load_key(pgp_key_public)['fingerprint']
               mail_body = pgpctx.encrypt_message(fingerprint, mail_body)

            # avoid waiting for the notification to send and instead rely on threads to handle it
            schedule_email(1, mail_address, mail_subject, mail_body)

    def refresh_tenant_states(self):
        # Remove selected onion services and add missing services
        if self.onion_service_job:
            def f(*args):
                return self.onion_service_job.add_all_hidden_services()

            self.onion_service_job.remove_unwanted_hidden_services().addBoth(f) # pylint: disable=no-member

        # Power cycle HTTPS processes
        def g(*args):
            return self.process_supervisor.maybe_launch_https_workers()

        self.process_supervisor.shutdown(friendly=True).addBoth(g)  # pylint: disable=no-member

    def format_and_send_mail(self, session, tid, user_desc, template_vars):
        subject, body = Templating().get_mail_subject_and_body(template_vars)

        if user_desc.get('pgp_key_public', ''):
            pgpctx = PGPContext(self.settings.tmp_path)
            fingerprint = pgpctx.load_key(user_desc['pgp_key_public'])['fingerprint']
            body = pgpctx.encrypt_message(fingerprint, body)

        session.add(models.Mail({
            'address': user_desc['mail_address'],
            'subject': subject,
            'body': body,
            'tid': tid,
        }))

    def get_tmp_file_by_path(self, path):
        for k, v in self.TempUploadFiles.items():
            if v.filepath == path:
                return self.TempUploadFiles.pop(k)

# State is a singleton class exported once
State = StateClass()
