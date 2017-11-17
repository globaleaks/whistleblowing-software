# -*- coding: utf-8
from datetime import datetime
from urllib2 import urlopen, Request

from OpenSSL.crypto import FILETYPE_PEM, dump_certificate

from globaleaks.utils.utility import log

# this import seems unused but it is required in order to load the mocks
from globaleaks.mocks import acme_mocks # pylint: disable=W0611

from acme import challenges, client, jose, messages


class ChallTok:
    def __init__(self, tok):
        self.tok = tok


def convert_asn1_date(asn1_bytes):
    return datetime.strptime(asn1_bytes,'%Y%m%d%H%M%SZ')


def register_account_key(directory_url, accnt_key):
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(directory_url, accnt_key)

    regr = acme.register()
    return regr.uri, regr.terms_of_service


def run_acme_reg_to_finish(domain, regr_uri, accnt_key, site_key, csr, tmp_chall_dict, directory_url):
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(directory_url, accnt_key)
    msg = messages.RegistrationResource(uri=regr_uri)
    regr = acme.query_registration(msg)

    log.info('Auto-accepting TOS: %s from: %s', regr.terms_of_service, directory_url)
    acme.agree_to_tos(regr)

    authzr = acme.request_challenges(
        identifier=messages.Identifier(typ=messages.IDENTIFIER_FQDN, value=domain))
    log.debug('Created auth client %s', authzr)

    def get_http_challenge(x, y):
        return y if isinstance(y.chall, challenges.HTTP01) else x

    challb = reduce(get_http_challenge, authzr.body.challenges, None)
    chall_tok = challb.chall.validation(accnt_key)

    v = chall_tok.split('.')[0]
    log.info('Exposing challenge on %s', v)
    tmp_chall_dict.set(v, ChallTok(chall_tok))

    test_path = 'http://localhost:8082{}'.format(challb.path)
    local_req = Request(test_path, headers={'Host': domain})
    log.debug('Testing local url path: %s', test_path)

    try:
        resp = urlopen(local_req)
        t = resp.read().decode('utf-8').strip()
        if t != chall_tok:
            raise ValueError
    except (IOError, ValueError):
        log.info('Resolving challenge locally failed. ACME request will fail. %s', test_path)
        raise

    cr = acme.answer_challenge(challb, challb.chall.response(accnt_key))
    log.debug('Acme CA responded to challenge request with: %s', cr)

    try:
        # Wrap this step and log the failure particularly here because this is
        # the expected point of failure for applications that are not reachable
        # from the public internet.
        cert_res, _ = acme.poll_and_request_issuance(jose.util.ComparableX509(csr), (authzr,))

        # NOTE pylint disabled due to spurious reporting. See docs:
        # https://letsencrypt.readthedocs.io/projects/acme/en/latest/api/jose/util.html#acme.jose.util.ComparableX509
        # pylint: disable=no-member
        cert_str = cert_res.body._dump(FILETYPE_PEM)
    except messages.Error as error:
        log.err("Failed in request issuance step %s", error)
        raise

    chain_certs = acme.fetch_chain(cert_res)

    # The chain certs returned by the LE CA will always have at least one
    # intermediate cert. Other certificate authorities that run ACME may
    # behave differently, but we aren't using them.
    chain_str = dump_certificate(FILETYPE_PEM, chain_certs[0])

    # pylint: disable=no-member
    expr_date = convert_asn1_date(cert_res.body.wrapped.get_notAfter())
    log.info('Retrieved cert using ACME that expires on %s', expr_date)

    return cert_str, chain_str
