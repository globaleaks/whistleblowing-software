# -*- coding: utf-8
import os
import re
import sys
import traceback

from twisted.internet import defer
from twisted.mail.smtp import SMTPError
from twisted.python.failure import Failure
from twisted.python.threadpool import ThreadPool

from globaleaks import __version__, orm
from globaleaks.models import AuditLog
from globaleaks.orm import tw
from globaleaks.settings import Settings
from globaleaks.transactions import db_schedule_email
from globaleaks.utils.agent import get_tor_agent, get_web_agent
from globaleaks.utils.crypto import sha256
from globaleaks.utils.log import log
from globaleaks.utils.mail import sendmail
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.sni import SNIMap
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.templating import Templating
from globaleaks.utils.token import TokenList
from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks.utils.utility import datetime_now
from globaleaks.utils.users_details_filter import UserDetailsFilter

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


class StateClass(ObjectDict, metaclass=Singleton):
    def __init__(self):
        self.settings = Settings

        self.tor_exit_set = TorExitSet()

        self.https_socks = []
        self.http_socks = []

        self.snimap = SNIMap()

        self.jobs = []
        self.jobs_monitor = None
        self.services = []
        self.onion_service_job = None

        self.exceptions = {}
        self.exceptions_email_count = 0
        self.stats_collection_start_time = datetime_now()

        self.accept_submissions = True

        self.tenant_state = {}
        self.tenant_cache = {}
        self.tenant_hostname_id_map = {}

        self.set_orm_tp(ThreadPool(4, 16))

        self.TempLogs = []
        self.TempKeys = TempDict(3600 * 72)
        self.TempUploadFiles = TempDict(3600)

        self.shutdown = False

    def init_environment(self):
        os.umask(0o77)
        self.settings.eval_paths()
        self.create_directories()
        self.cleaning_dead_files()
        self.tokens = TokenList(self, self.settings.tmp_path)

    def set_orm_tp(self, orm_tp):
        self.orm_tp = orm_tp
        orm.set_thread_pool(orm_tp)

    def get_agent(self):
        if self.tenant_cache[1].anonymize_outgoing_connections:
            return get_tor_agent(self.settings.socks_host, self.settings.socks_port)

        return get_web_agent()

    def log(self, **kwargs):
        entry = AuditLog()

        for key, value in kwargs.items():
            setattr(entry, key, value)

        self.TempLogs.append(entry)

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
            log.debug("Error in creating directory: %s (%s)",
                      path, excep.strerror)
            raise excep

        return True

    def create_directories(self):
        """
        Execute some consistency checks on command provided GlobaLeaks paths

        if one of working_path or static path is created we copy
        here the static files (default logs, and in the future pot files for localization)
        because here stay all the files needed by the application except the python scripts
        """
        for dirpath in [self.settings.working_path,
                        self.settings.files_path,
                        self.settings.attachments_path,
                        self.settings.tmp_path,
                        self.settings.log_path]:
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
                result = re.compile(self.settings.AES_file_regexp).match(f)
                if result is not None:
                    if not os.path.isfile("%s%s" % (keypath, result.group(1))):
                        log.debug("Removing old encrypted file (lost key): %s", path)
                        os.remove(path)
            except Exception as excep:
                log.debug("Error while evaluating removal for %s: %s", path, excep)

    def reset_hourly(self):
        for tid in self.tenant_state:
            self.tenant_state[tid] = TenantState(self)

        self.exceptions.clear()
        self.exceptions_email_count = 0

        self.stats_collection_start_time = datetime_now()

    def sendmail(self, tid, to_address, subject, body):
        if self.settings.disable_notifications:
            return defer.succeed(True)

        if self.tenant_cache[tid].mode != 'default':
            tid = 1

        return sendmail(tid,
                        self.tenant_cache[tid].notification.smtp_server,
                        self.tenant_cache[tid].notification.smtp_port,
                        self.tenant_cache[tid].notification.smtp_security,
                        self.tenant_cache[tid].notification.smtp_authentication,
                        self.tenant_cache[tid].notification.smtp_username,
                        self.tenant_cache[tid].notification.smtp_password,
                        self.tenant_cache[tid].name,
                        self.tenant_cache[tid].notification.smtp_source_email,
                        to_address,
                        self.tenant_cache[tid].name + ' - ' + subject,
                        body,
                        self.tenant_cache[1].anonymize_outgoing_connections,
                        self.settings.socks_host,
                        self.settings.socks_port)

    def schedule_exception_email(self, tid, exception_text, *args):
        if not hasattr(self.tenant_cache[tid], 'notification'):
            log.err("Error: Cannot send mail exception before complete initialization.")
            return

        if self.exceptions_email_count >= self.settings.exceptions_email_hourly_limit:
            return

        exception_text = (exception_text % args) if args else exception_text

        sha256_hash = sha256(exception_text.encode())

        if sha256_hash not in self.exceptions:
            self.exceptions[sha256_hash] = 0

        self.exceptions[sha256_hash] += 1
        if self.exceptions[sha256_hash] > 5:
            log.err("Exception mail suppressed for (%s) [reason: threshold exceeded]", sha256_hash)
            return

        self.exceptions_email_count += 1

        mail_subject = "GlobaLeaks Exception"
        delivery_list = self.tenant_cache[1].notification.exception_delivery_list

        for mail_address, pgp_key_public in delivery_list:
            mail_body = "Platform: %s\nHost: %s (%s)\nVersion: %s\n\n%s" % (self.tenant_cache[tid].name,
                                                                            self.tenant_cache[tid].hostname,
                                                                            self.tenant_cache[tid].onionservice,
                                                                            __version__,
                                                                            exception_text)

            # Opportunisticly encrypt the mail body. NOTE that mails will go out
            # unencrypted if one address in the list does not have a public key set.
            if pgp_key_public:
                pgpctx = PGPContext(self.settings.tmp_path)
                fingerprint = pgpctx.load_key(pgp_key_public)['fingerprint']
                mail_body = pgpctx.encrypt_message(fingerprint, mail_body)

            # avoid waiting for the notification to send and instead rely on threads to handle it
            tw(db_schedule_email, 1, mail_address, mail_subject, mail_body)

    def refresh_connection_endpoints(self):
        # Remove selected onion services and add missing services
        if self.onion_service_job is not None:
            def f(*args):
                return self.onion_service_job.add_all_onion_services()

            self.onion_service_job.remove_unwanted_onion_services().addBoth(f)  # pylint: disable=no-member

    def format_and_send_mail(self, session, tid, user_desc, template_vars):
        subject, body = Templating().get_mail_subject_and_body(template_vars)

        if user_desc.get('pgp_key_public', ''):
            pgpctx = PGPContext(self.settings.tmp_path)
            fingerprint = pgpctx.load_key(user_desc['pgp_key_public'])['fingerprint']
            body = pgpctx.encrypt_message(fingerprint, body)

        db_schedule_email(session, tid, user_desc['mail_address'], subject, body)

    def get_tmp_file_by_name(self, filename):
        for k, v in self.TempUploadFiles.items():
            if os.path.basename(v.filepath) == filename:
                return self.TempUploadFiles.pop(k)


def mail_exception_handler(etype, value, tback):
    """
    Formats traceback and exception data and emails the error,
    This would be enabled only in the testing phase and testing release,
    not in production release.
    """
    if isinstance(value, (GeneratorExit,
                          defer.AlreadyCalledError,
                          SMTPError)) or \
        (etype == AssertionError and value.message == "Request closed"):
        # we need to bypass email notification for some exception that:
        # 1) raise frequently or lie in a twisted bug;
        # 2) lack of useful stacktraces;
        # 3) can be cause of email storm amplification
        #
        # this kind of exception can be simply logged error logs.
        log.err("exception mail suppressed for exception (%s) [reason: special exception]", str(etype))
        return

    mail_body = ""

    # collection of the stacktrace info
    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                      "", str(etype))

    mail_body += "%s %s\n\n" % (exc_type.strip(), etype.__doc__)

    mail_body += '\n'.join(traceback.format_exception(etype, value, tback))

    log.err("Unhandled exception raised:")
    log.err(mail_body)
    user_filter = UserDetailsFilter(mail_body)
    mail_body = user_filter.filtered_string()
    State.schedule_exception_email(1, mail_body)


def extract_exception_traceback_and_schedule_email(e):
    if isinstance(e, Failure):
        type, value, traceback = e.type, e.value, e.getTracebackObject()
    else:
        type, value, traceback = sys.exc_info()

    mail_exception_handler(type, value, traceback)


# State is a singleton class exported once
State = StateClass()
