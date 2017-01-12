from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import PrivateFactory
from globaleaks.rest import requests
from globaleaks.rest import errors
from globaleaks.utils.utility import log


def check_tls(priv_key, cert, chain):
    if (priv_key == 'throw'):
        raise errors.InvalidInputFormat('Dummy exception raised')
    return True


@transact
def configure_tls(store, request):
    # TODO validate config params with SSL logic

    pk, cert, chain = request['priv_key'], request['cert'], request['chain']
    
    privFact = PrivateFactory(store)

    privFact.set_val('tls_priv_key', pk)
    privFact.set_val('tls_cert', cert)
    privFact.set_val('tls_chain', chain)

    check_tls(pk, cert, chain)


@transact
def delete_tls(store):
    privFact = PrivateFactory(store)

    privFact.set_val('tls_priv_key', u'')
    privFact.set_val('tls_cert', u'')
    privFact.set_val('tls_chain', u'')


class CertFileHandler(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        req = self.validate_message(self.request.body, requests.AdminTLSCertFilesConfigDesc)

        try:
          yield configure_tls(req)
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self):
        try:
          yield delete_tls()
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)

class ConfigHandler(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def get(self):
        https_cfg = {
            'state': 'empty',
            'cert': 'py-back',
            'priv_key': '',
            'chain': '',
        }
        self.write(https_cfg)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self):
        # TODO Reset and delete all config
        self.set_status(200)

@transact
def generate_csr(store, request):
    from globaleaks.security import generateRandomSalt
    fake_csr = "============certificate request============\n"+'\n'.join([generateRandomSalt() for i in range(5)])+'\n==========================================='

    return fake_csr

class CSRConfigHandler(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.body, requests.AdminCSRConfigDesc)

        try:
          csr = yield generate_csr(request)
          self.write(csr)
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)
