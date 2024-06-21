# -*- coding: utf-8 -*-

from globaleaks.orm import transact
from datetime import datetime
from globaleaks import models

def serialize_auditlog(log):
    return {
        'date': log.date,
        'type': log.type,
        'user_id': log.user_id,
        'object_id': log.object_id,
        'data': log.data
    }

def serialize_comment_log(log):
    """
    Serialize an audit log entry for external use.
    """
    return {
        'id': log['object_id'],
        'creation_date': log['date'],
        'content': log.get('content', 'changed'),
        'author_id': log['user_id'],
        'visibility': 'public',
        'type': 'auditlog'
    }

def get_label(session, label_id, table):
    """
    Fetch the label for a given UUID from the specified table.
    """
    result = session.query(table).filter_by(id=label_id).first()
    return result.label['en'] if result else f"Unknown {table.__tablename__}"

def get_audit_log(session, object_id):
    """
    Fetch audit logs for a given object_id where the type is 'update_report_status'.
    """
    logs = session.query(models.AuditLog).filter(
        models.AuditLog.object_id == object_id,
        models.AuditLog.type == 'update_report_status'
    )
    return [serialize_auditlog(log) for log in logs]

def format_date(date):
    """
    Format the date to the desired string format.
    """
    return date.strftime("%B %d, %Y")

def get_user_name(session, user_id):
    """
    Retrieve the user's name given their user ID.
    """
    user = session.query(models.User).filter_by(id=user_id).one_or_none()
    return user.name if user else 'Unknown User'

@transact
def process_logs(session, tip ,tip_id):
    """
    Process a list of logs to append their details to a tip dictionary.
    """
    logs = get_audit_log(session,tip_id)
    for log in logs:
        status_change_string = "changed"
        status_details = log.get('data', {})

        if isinstance(status_details, dict):
            status = status_details.get('status')
            sub_status = status_details.get('substatus')

            if status:
                status_label = get_label(session, status, models.SubmissionStatus)
                status_change_string = f"changed -> {status_label}"

                if sub_status:
                    sub_status_label = get_label(session, sub_status, models.SubmissionSubStatus)
                    status_change_string += f" - {sub_status_label}"

        author_name = get_user_name(session, log['user_id'])
        formatted_date = format_date(log['date'])
        formatted_content = (f"Author: {author_name}\n"
                             f"Date: {formatted_date}\n"
                             f"Status: {status_change_string}")

        log['content'] = formatted_content
        tip['comments'].append(serialize_comment_log(log))

    return tip
