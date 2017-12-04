# -*- coding: utf-8
#
# wizard
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.admin import tenant
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.node import update_enabled_languages
from globaleaks.handlers.admin.user import db_create_user, db_create_receiver_user
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import config, l10n, profiles
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.utils.utility import log, datetime_null


@transact
def wizard(store, tid, request, language):
    update_enabled_languages(store, tid, [language], language)

    tenant = models.db_get(store, models.Tenant, id=tid)
    tenant.label = request['node_name']

    node = config.NodeFactory(store, tid)

    if node.get_val(u'wizard_done'):
        log.err("DANGER: Wizard already initialized!", tid=tid)
        raise errors.ForbiddenOperation

    node._query_group()

    node.set_val(u'name', request['node_name'])
    node.set_val(u'default_language', language)
    node.set_val(u'wizard_done', True)

    node_l10n = l10n.NodeL10NFactory(store, tid)

    node_l10n.set_val(u'header_title_homepage', language, request['node_name'])

    profiles.load_profile(store, tid, request['profile'])

    receiver_desc = models.User().dict(language)
    receiver_desc['name'] = request['receiver_name']
    receiver_desc['username'] = u'recipient'
    receiver_desc['name'] = receiver_desc['public_name'] = request['receiver_name']
    receiver_desc['mail_address'] = request['receiver_mail_address']
    receiver_desc['language'] = language
    receiver_desc['role'] =u'receiver'
    receiver_desc['deletable'] = True
    receiver_desc['pgp_key_remove'] = False

    _, receiver = db_create_receiver_user(store, tid, receiver_desc, language)

    context_desc = models.Context().dict(language)
    context_desc['name'] = u'Default'
    context_desc['receivers'] = [receiver.id]

    context = db_create_context(store, tid, context_desc, language)

    admin_desc = models.User().dict(language)
    admin_desc['username'] = u'admin'
    admin_desc['password'] = request['admin_password']
    admin_desc['name'] = admin_desc['public_name'] = request['admin_name']
    admin_desc['mail_address'] = request['admin_mail_address']
    admin_desc['language'] = language
    admin_desc['role'] =u'admin'
    admin_desc['deletable'] = False
    admin_desc['pgp_key_remove'] = False
    admin_desc['password_change_needed'] = False

    db_create_user(store, tid, admin_desc, language)

    db_refresh_memory_variables(store)


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    check_roles = 'unauthenticated'
    invalidate_cache = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.WizardDesc)

        return wizard(self.request.tid, request, self.request.language)
