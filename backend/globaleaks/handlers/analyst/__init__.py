# -*- coding: utf-8 -*-
#
# Handlers dealing with analyst user functionalities
from sqlalchemy.sql.expression import func, and_

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact


@transact
def get_stats(session, tid):
    """
    Transaction for retrieving analyst statistics

    :param session: An ORM session
    :param tid: A tenant ID
    """
    reports_count = session.query(func.count(models.InternalTip.id)) \
                           .filter(models.InternalTip.tid == tid).one()[0]

    num_tips_no_access = session.query(func.count(models.InternalTip.id)) \
                                .filter(models.InternalTip.tid == tid,
                                        models.InternalTip.access_count == 0).one()[0]

    num_tips_mobile = session.query(func.count(models.InternalTip.id)) \
                             .filter(models.InternalTip.tid == tid,
                                     models.InternalTip.mobile == True).one()[0]

    num_tips_tor = session.query(func.count(models.InternalTip.id)) \
                             .filter(models.InternalTip.tid == tid,
                                     models.InternalTip.tor == True).one()[0]

    num_subscribed_tips = session.query(func.count(models.InternalTip.id)) \
                                 .filter(models.InternalTip.tid == tid) \
                                 .join(models.InternalTipData,
                                       and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                            models.InternalTipData.key == 'whistleblower_identity',
                                            models.InternalTipData.creation_date == models.InternalTip.creation_date)).one()[0]

    num_initially_anonymous_tips = session.query(func.count(models.InternalTip.id)) \
                                       .filter(models.InternalTip.tid == tid) \
                                       .join(models.InternalTipData,
                                             and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                                  models.InternalTipData.key == 'whistleblower_identity',
                                                  models.InternalTipData.creation_date != models.InternalTip.creation_date)).one()[0]

    num_anonymous_tips = reports_count - num_subscribed_tips - num_initially_anonymous_tips

    return {
        "reports_count": reports_count,
        "reports_with_no_access": num_tips_no_access,
        "reports_anonymous": num_anonymous_tips,
        "reports_subscribed": num_subscribed_tips,
        "reports_initially_anonymous": num_initially_anonymous_tips,
        "reports_mobile": num_tips_mobile,
        "reports_tor": num_tips_tor
    }


class Statistics(BaseHandler):
    """
    Handler for statistics fetch
    """
    check_roles = 'analyst'

    def get(self):
        return get_stats(self.session.tid)
