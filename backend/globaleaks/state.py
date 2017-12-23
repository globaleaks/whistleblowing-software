# -*- coding: utf-8
import sys

from storm import tracer

from twisted.internet import defer
from twisted.python.threadpool import ThreadPool

from globaleaks import __version__, orm
from globaleaks.utils.agent import get_tor_agent, get_web_agent
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.objectdict import ObjectDict
from globaleaks.security import encrypt_message, sha256
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks.utils.utility import datetime_now, log
from globaleaks.utils.tempdict import TempDict

def getAlarm(settings):
    from globaleaks.anomaly import Alarm
    return Alarm(settings)


class TenantState(object):
    def __init__(self, settings):
        self.RecentEventQ = []
        self.EventQ = []
        self.AnomaliesQ = []

        # An ACME challenge will have 5 minutes to resolve
        self.acme_tmp_chall_dict = TempDict(300)

        self.Alarm = getAlarm(settings)


class StateClass(ObjectDict):
    __metaclass__ = Singleton

    orm_tp = ThreadPool(1, 1)

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

        self.tenant_cache[1] = ObjectDict({
            'maximum_filesize': 30,
            'allow_iframes_inclusion': False,
            'accept_tor2web_access': {
                'admin': True,
                'whistleblower': False,
                'custodian': False,
                'receiver': False
            },
            'private': {
                'https_enabled': False,
            },
            'anonymize_outgoing_connections': True,
        })

        tracer.debug(self.settings.orm_debug, sys.stdout)
        self.set_orm_tp(self.orm_tp)

        self.TempUploadFiles = TempDict(timeout=3600)

    def set_orm_tp(self, orm_tp):
        self.orm_tp = orm_tp
        orm.set_thread_pool(orm_tp)

    def get_agent(self, tid=1):
        if self.tenant_cache[tid].anonymize_outgoing_connections:
            return get_tor_agent(self.settings.socks_host, self.settings.socks_port)

        return get_web_agent()

    def get_mail_counter(self, receiver_id):
        return self.mail_counters.get(receiver_id, 0)

    def increment_mail_counter(self, receiver_id):
        self.mail_counters[receiver_id] = self.mail_counters.get(receiver_id, 0) + 1

    def reset_hourly(self):
        for tid in self.tenant_state:
            self.tenant_state[tid] = TenantState(self.settings)

        self.exceptions.clear()
        self.exceptions_email_count = 0
        self.mail_counters.clear()

        self.stats_collection_start_time = datetime_now()

    def sendmail(self, tid, to_address, subject, body):
       if self.settings.testing:
           # during unit testing do not try to send the mail
           return defer.succeed(True)

       return sendmail(tid,
                       self.tenant_cache[tid].notification.username,
                       self.tenant_cache[tid].private.smtp_password,
                       self.tenant_cache[tid].notification.server,
                       self.tenant_cache[tid].notification.port,
                       self.tenant_cache[tid].notification.security,
                       self.tenant_cache[tid].notification.source_name,
                       self.tenant_cache[tid].notification.source_email,
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

        exception_text = bytes("Platform: %s (%s)\nVersion: %s\n\n%s" \
                               % (self.tenant_cache[1].hostname,
                                  self.tenant_cache[1].onionservice,
                                  __version__,
                                  exception_text))

        for mail_address, pub_key in delivery_list:
            mail_body = exception_text

            # Opportunisticly encrypt the mail body. NOTE that mails will go out
            # unencrypted if one address in the list does not have a public key set.
            if pub_key:
                mail_body = encrypt_message(pub_key, mail_body)

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


# State is a singleton class exported once
State = StateClass()
