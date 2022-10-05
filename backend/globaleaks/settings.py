# -*- coding: utf-8
import getpass
import grp
import os
import pwd
import sys

from globaleaks.orm import make_db_uri, set_db_uri, enable_orm_debug
from globaleaks.utils.singleton import Singleton

this_directory = os.path.dirname(__file__)

possible_client_paths = [
    '/usr/share/globaleaks/client/',
    os.path.abspath(os.path.join(this_directory, '../../client/build/')),
    os.path.abspath(os.path.join(this_directory, '../../client/app/'))
]


class SettingsClass(object, metaclass=Singleton):
    def __init__(self):
        # daemonize the process
        self.nodaemon = False

        self.bind_address = '::'
        self.bind_remote_ports = [80, 443]
        self.bind_local_ports = [8080, 8082, 8083, 8443]

        self.db_type = 'sqlite'

        # debug defaults
        self.orm_debug = False

        # files and paths
        self.src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.backend_script = os.path.abspath(os.path.join(self.src_path, 'globaleaks/backend.py'))

        self.ramdisk_path = '/dev/shm/globaleaks'
        self.working_path = '/var/globaleaks'

        self.authentication_lifetime = 1800

        self.accept_submissions = True

        # statistical, referred to latest period
        # and resetted by session_management sched
        self.failed_login_attempts = {}

        self.local_hosts = ['127.0.0.1', 'localhost']

        self.onionservice = None

        # Default request time uniform value
        self.side_channels_guard = 150

        # SOCKS default
        self.socks_host = "127.0.0.1"
        self.socks_port = 9050

        self.rsa_key_bits = 4096
        self.csr_sign_bits = 512

        self.disable_notifications = False
        self.notification_limit = 30
        self.jobs_operation_limit = 20

        self.user = getpass.getuser()

        self.uid = os.getuid()
        self.gid = os.getgid()

        self.devel_mode = False
        self.disable_csp = False

        # Number of failed login enough to generate an alarm
        self.failed_login_alarm = 5

        # Number of minutes in which a user is prevented to login in case of triggered alarm
        self.failed_login_block_time = 5

        # Limit for log sizes and number of log files
        # https://github.com/globaleaks/GlobaLeaks/issues/1578
        self.log_size = 10000000  # 10MB
        self.log_file_size = 1000000  # 1MB
        self.num_log_files = self.log_size / self.log_file_size

        self.AES_file_regexp = r'(.*)\.aes'
        self.AES_keyfile_prefix = "aeskey-"

        self.exceptions_email_hourly_limit = 20

        self.enable_input_length_checks = True

        self.mail_timeout = 15  # seconds
        self.mail_attempts_limit = 3  # per mail limit

        self.acme_directory_url = 'https://acme-v02.api.letsencrypt.org/directory'

        self.enable_api_cache = True

    def eval_paths(self):
        self.pidfile_path = os.path.join(self.working_path, 'globaleaks.pid')

        self.files_path = os.path.abspath(os.path.join(self.working_path, 'files'))
        self.scripts_path = os.path.abspath(os.path.join(self.working_path, 'scripts'))
        self.attachments_path = os.path.abspath(os.path.join(self.working_path, 'attachments'))
        self.tmp_path = os.path.abspath(os.path.join(self.working_path, 'tmp'))

        self.db_file_path = os.path.abspath(os.path.join(self.working_path, 'globaleaks.db'))

        self.log_path = os.path.abspath(os.path.join(self.working_path, 'log'))
        self.logfile = os.path.abspath(os.path.join(self.log_path, 'globaleaks.log'))
        self.accesslogfile = os.path.abspath(os.path.join(self.log_path, "access.log"))

        # Client path detection
        possible_client_paths.insert(0, os.path.join(self.working_path, 'client'))
        for path in possible_client_paths:
            if os.path.isfile(os.path.join(path, 'index.html')):
                self.client_path = path
                break

        if not self.client_path:
            print("Unable to find a directory to load the client from")
            sys.exit(1)

        self.appdata_file = os.path.join(self.client_path, 'data/appdata.json')
        self.questionnaires_path = os.path.join(self.client_path, 'data/questionnaires')
        self.questions_path = os.path.join(self.client_path, 'data/questions')
        self.field_attrs_file = os.path.join(self.client_path, 'data/field_attrs.json')

        set_db_uri(make_db_uri(self.db_file_path))

    def set_devel_mode(self):
        self.devel_mode = True
        self.rsa_key_bits = 1024
        self.acme_directory_url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        self.bind_remote_ports = []
        self.working_path = os.path.join(self.src_path, 'workingdir')

    def load_cmdline_options(self, options):
        self.nodaemon = options.nodaemon
        self.disable_csp = options.disable_csp
        self.bind_address = options.ip
        self.socks_host = options.socks_host
        self.socks_port = options.socks_port

        if options.user:
            self.user = options.user
            self.uid = pwd.getpwnam(options.user).pw_uid
            self.gid = grp.getgrnam(options.user).gr_gid

        if options.devel_mode:
            self.set_devel_mode()

        if options.orm_debug:
            enable_orm_debug()

        if options.working_path:
            self.working_path = options.working_path


# Settings is a singleton class exported once
Settings = SettingsClass()
