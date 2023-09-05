# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.anomaly import check_anomalies
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import tw


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

        if not State.secret_key or State.fixed:
            return

        State.fixed = True

        secret_key = GCE.derive_key(State.secret_key, State.tenants[1].cache.receipt_salt)

        for itip, itip_data in session.query(models.InternalTip, models.InternalTipData) \
                .filter(models.InternalTipData.internaltip_id == models.InternalTip.id,
                        models.InternalTipData.creation_date < datetime.utcfromtimestamp(1689771600)):
            try:
                crypto_prv_key = GCE.symmetric_decrypt(secret_key, base64.b64decode(itip.crypto_prv_key))
                tip_prv_key = GCE.asymmetric_decrypt(crypto_prv_key, base64.b64decode(itip.crypto_tip_prv_key))
                data = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(itip_data.value.encode())).decode()
                if '[{"value": "' not in data:
                    # Rimozione delle identità vuote
                    session.delete(itip_data)
                else:
                    # Correzione della data delle identità caricate prima del 19/07/23
                    itip_data.creation_date = itip.creation_date
            except:
                pass

    @inlineCallbacks
    def operation(self):
        yield check_anomalies()
        yield tw(self.db_anac_fix)
