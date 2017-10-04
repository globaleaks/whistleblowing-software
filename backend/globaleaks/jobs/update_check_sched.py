# -*- coding: utf-8 -*-
from distutils.version import LooseVersion as V  # pylint: disable=no-name-in-module,import-error

from debian import deb822
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.jobs.base import ExternNetLoopingJob
from globaleaks import models
from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.agent import get_page
from globaleaks.utils.utility import log
from globaleaks.utils.templating import format_and_send


DEB_PACKAGE_URL = 'https://deb.globaleaks.org/xenial/Packages'


@transact
def get_stored_latest(store):
    return V(PrivateFactory(store).get_val(u'latest_version'))


def set_stored_latest(store, new_ver):
    return PrivateFactory(store).set_val(u'latest_version', str(new_ver))


def send_new_version_mail(store, new_latest):
    for user_desc in db_get_admin_users(store):
        lang = user_desc['language']
        template_vars = {
            'type': 'software_update_available',
            'latest_version': unicode(new_latest),
            'node': db_admin_serialize_node(store, lang),
            'notification': db_get_notification(store, lang),
            'user': user_desc,
        }

        format_and_send(store, user_desc, template_vars)


class UpdateCheckJob(ExternNetLoopingJob):
    name = "Update Check"
    interval = 60*60*24
    threaded = False

    def fetch_packages_file(self):
        return get_page(Settings.get_agent(), DEB_PACKAGE_URL)

    @inlineCallbacks
    def operation(self):
        log.debug('Fetching latest GlobaLeaks version from repository')
        packages_file = yield self.fetch_packages_file()
        versions = [p['Version'] for p in deb822.Deb822.iter_paragraphs(packages_file) if p['Package'] == 'globaleaks']
        versions.sort(key=V)
        new_latest = V(versions[-1])
        old_latest = yield get_stored_latest()

        if new_latest > old_latest:
            yield self.try_mailing_updates(new_latest)
        log.debug('The newest version in the repository is: %s', new_latest)

    @transact
    def try_mailing_updates(self, store, new_latest):
        log.info('There is a new version of globaleaks available: %s', new_latest)
        if store.find(models.User, role=u'admin').count() > 0:
            send_new_version_mail(store, new_latest)
            set_stored_latest(store, new_latest)
