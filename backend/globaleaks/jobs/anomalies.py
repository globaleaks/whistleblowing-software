# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.anomaly import check_anomalies
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import tw


def get_stats(session, models):
    return {"num_internal_tip":      session.query(models.InternalTip).count(),
            "num_internal_tip_data": session.query(models.InternalTipData).count(),
            "num_eq_dates":          session.query(models.InternalTip, models.InternalTipData).filter(
                models.InternalTip.id == models.InternalTipData.internaltip_id,
                models.InternalTip.creation_date == models.InternalTipData.creation_date).count(),
            "num_ne_dates":          session.query(models.InternalTip, models.InternalTipData).filter(
                models.InternalTip.id == models.InternalTipData.internaltip_id,
                models.InternalTip.creation_date != models.InternalTipData.creation_date).count()}

class Anomalies(LoopingJob):
    """
    This job checks for anomalies and take care of saving them on the db.
    """
    interval = 60

    def db_anac_fix(self, session):
        import base64
        import json
        from datetime import datetime
        from globaleaks import models
        from globaleaks.state import State
        from globaleaks.utils.crypto import GCE
        from globaleaks.utils.log import log

        if not State.secret_key or State.fixed:
            return

        State.fixed = True

        secret_key = GCE.derive_key(State.secret_key, State.tenants[1].cache.receipt_salt)

        stats_before_fix = get_stats(session, models)

        num_deletions, num_corrections = 0, 0
        log.err("START FIX ANAC SEGNALAZIONE ANONIME")
        log.err("num_deletions = {}".format(num_deletions))
        log.err("num_corrections = {}".format(num_deletions))
        log.err("stats = {}".format(stats_before_fix))
        for itip, itip_data in session.query(models.InternalTip, models.InternalTipData) \
                                      .filter(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                              models.InternalTip.creation_date < datetime.fromtimestamp(1689771600)):
            try:
                crypto_prv_key = GCE.symmetric_decrypt(secret_key, base64.b64decode(itip.crypto_prv_key))
                tip_prv_key = GCE.asymmetric_decrypt(crypto_prv_key, base64.b64decode(itip.crypto_tip_prv_key))
                data = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(itip_data.value.encode())).decode()
                if '[{"value": "' not in data:
                    # Rimozione delle identità vuote
                    session.delete(itip_data)
                    num_deletions += 1
                    log.err("RIMOZIONE IDENTITA PROGRESSIVE: {}".format(itip.progressive))
                else:
                    # Correzione della data delle identità caricate prima del 19/07/23
                    itip_data.creation_date = itip.creation_date
                    num_corrections += 1
                    log.err("CORREZIONE DATA PROGRESSIVE: {}".format(itip.progressive))
            except:
                pass

        stats_after_fix = get_stats(session, models)
        log.err("END FIX ANAC SEGNALAZIONE ANONIME")
        log.err("num_deletions = {}".format(num_deletions))
        log.err("num_corrections = {}".format(num_deletions))
        log.err("stats = {}".format(stats_after_fix))

    @inlineCallbacks
    def operation(self):
        yield check_anomalies()
        yield tw(self.db_anac_fix)
