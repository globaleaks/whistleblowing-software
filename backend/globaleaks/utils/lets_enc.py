"""Example script showing how to use acme client API."""
import os, pkg_resources
from datetime import datetime
from urllib2 import urlopen

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from OpenSSL.crypto import FILETYPE_PEM, dump_certificate

from acme import client
from acme import messages
from acme import jose
from acme import challenges

from globaleaks.utils.utility import log


DIRECTORY_URL = 'https://acme-staging.api.letsencrypt.org/directory'
#DIRECTORY_URL = 'https://acme-v01.api.letsencrypt.org/directory'
BITS = 2048  # TODO minimum for Boulder


class ChallTok():
    def __init__(self, tok):
        self.tok = tok

def convert_asn1_date(asn1_bytes):
    return datetime.strptime(asn1_bytes,'%y%m%d%H%M%SZ')

def register_account_key(accnt_key):
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(DIRECTORY_URL, accnt_key)

    regr = acme.register()
    return regr.uri, regr.terms_of_service


def run_acme_reg_to_finish(domain, regr_uri, accnt_key, site_key, csr, tmp_chall_dict):
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(DIRECTORY_URL, accnt_key)
    msg = messages.RegistrationResource(uri=regr_uri)
    regr = acme.query_registration(msg)

    log.info('Auto-accepting TOS: %s from: %s' % (regr.terms_of_service, DIRECTORY_URL))
    acme.agree_to_tos(regr)

    authzr = acme.request_challenges(
        identifier=messages.Identifier(typ=messages.IDENTIFIER_FQDN, value=domain))
    log.debug('Created auth client %s' % authzr)

    def get_http_challenge(x, y):
         if type(y.chall) is challenges.HTTP01:
            return y
         else:
            return x

    challb = reduce(get_http_challenge, authzr.body.challenges, None)
    chall_tok = challb.chall.validation(accnt_key)

    # TODO author tests to ensure that chall token expires
    v = chall_tok.split('.')[0]
    log.info('Exposing challenge on %s' % v)
    tmp_chall_dict.set(v, ChallTok(chall_tok))

    try:
       domain = 'localhost:8082'
       test_path = 'http://{0}{1}'.format(domain, challb.path)
       log.debug('Testing local url path: %s' % test_path)
       resp = urlopen(test_path)
       t = resp.read().decode('utf-8').strip()
       assert t == chall_tok
    except (IOError, AssertionError) as e:
       log.info('Resolving challenge locally failed. ACME request will fail. %s' % test_path)
       raise e

    challr = challenges.HTTP01Response()

    cr = acme.answer_challenge(challb, challb.chall.response(accnt_key))
    log.debug('Acme CA responded to challenge with: %s' % cr)

    try:
        # Wrap this step and log the failure particularly here because this is
        # the expected point of failure for applications that are not reachable
        # from the public internet.
        cert_res, _ = acme.poll_and_request_issuance(jose.util.ComparableX509(csr), (authzr,))
    except messages.Error as error:
        log.err("Failed in request issueance step {0}".format(error))
        raise error

    chain_certs = acme.fetch_chain(cert_res)

    # The chain certs returned by the LE CA will always have at least one
    # intermediate cert. Other certificate authorities that run ACME may
    # behave differently, but we aren't using them.
    chain_str = dump_certificate(FILETYPE_PEM, chain_certs[0])

    expr_date = convert_asn1_date(cert_res.body.wrapped.get_notAfter())
    log.info('Retrieved cert using ACME that expires on %s' % expr_date)

    return cert_res.body._dump(FILETYPE_PEM), chain_str
