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
    num_tips = session.query(func.count(models.InternalTip.id)).one()[0]

    num_tips_no_access = session.query(func.count(models.InternalTip.id)) \
                                .filter(models.InternalTip.access_count == 0).one()[0]

    num_tips_at_least_one_access = num_tips - num_tips_no_access

    num_subscribed_tips = session.query(func.count(models.InternalTip.id)) \
                                .join(models.InternalTipData,
                                      and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                           models.InternalTipData.key == 'whistleblower_identity',
                                           models.InternalTipData.creation_date == models.InternalTip.creation_date)).one()[0]

    num_subscribed_later_tips = session.query(func.count(models.InternalTip.id)) \
                                .join(models.InternalTipData,
                                      and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                           models.InternalTipData.key == 'whistleblower_identity',
                                           models.InternalTipData.creation_date != models.InternalTip.creation_date)).one()[0]

    num_anonymous_tips = num_tips - num_subscribed_tips - num_subscribed_later_tips

    return {
        "reports_with_no_access": num_tips_no_access,
        "reports_with_at_least_one_access": num_tips_at_least_one_access,
        "reports_anonymous": num_anonymous_tips,
        "reports_subscribed": num_subscribed_tips,
        "reports_subscribed_later": num_subscribed_later_tips,
    }


class Statistics(BaseHandler):
    """
    Handler for statistics fetch
    """
    check_roles = 'analyst'

    def get(self):
        return get_stats(self.session.tid)
