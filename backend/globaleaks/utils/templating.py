# -*- encoding: utf-8 -*-
#
# this file contain the class converting the %KeyWords% with data.
# perhaps exists something python-stable-portable-well know, this
# class has just be written down easily and fit our needs.
#
# If you know something better, please tell to us. At the moment,
# supporter KeyWords are here documented:
# https://github.com/globaleaks/GlobaLeaks/wiki/Customization-guide#customize-notification

import collections
import copy

from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import ISO8601_to_pretty_str, ISO8601_to_day_str, \
    ISO8601_to_datetime, datetime_now, bytes_to_pretty_str

node_keywords = [
    '{NodeName}',
    '{HiddenService}',
    '{PublicSite}'
]

context_keywords = [
    '{ContextName}'
]

receiver_keywords = [
    '{RecipientName}'
]

tip_keywords = [
    '{TipID}',
    '{TipNum}',
    '{TipLabel}',
    '{EventTime}',
    '{SubmissionDate}',
    '{ExpirationDate}',
    '{ExpirationWatch}',
    '{QuestionnaireAnswers}',
    '{Comments}',
    '{Messages}',
    '{TorUrl}',
    '{HTTPSUrl}'
]

file_keywords = [
    '{FileName}',
    '{FileSize}'
]

export_message_keywords = [
    '{Content}'
]

expiration_summary_keywords = [
    '{ExpiringSubmissionCount}',
    '{EarliestExpirationDate}',
    '{TorUrl}',
    '{HTTPSUrl}'
]

admin_pgp_alert_keywords = [
    '{PGPKeyInfoList}'
]

user_pgp_alert_keywords = [
    '{PGPKeyInfo}'
]

admin_anomaly_keywords = [
    '{AnomalyDetailDisk}',
    '{AnomalyDetailActivities}',
    '{ActivityAlarmLevel}',
    '{ActivityDump}',
    '{NodeName}',
    '{FreeMemory}',
    '{TotalMemory}'
]

https_expr_keywords = [
    '{ExpirationDate}',
    '{TorUrl}',
]


def indent(n=1):
    return '  ' * n


def indent_text(text, n=1):
    """
    Add n * 2 space as indentation to each of the non empty lines of the provided text
    """
    return '\n'.join([('  ' * n if not l.isspace() else '') + l for l in text.splitlines()])


class Keyword(object):
    keyword_list = []
    data_keys = []

    def __init__(self, data):
        for k in self.data_keys:
            if k not in data:
                raise errors.InternalServerError('Missing key \'%s\' while resolving template \'%s\'' % (k, type(self).__name__))

        self.data = data


class NodeKeyword(Keyword):
    keyword_list = node_keywords
    data_keys = ['node', 'notification']

    def NodeName(self):
        return self.data['node']['name']

    def HiddenService(self):
        return 'http://' + self.data['node']['onionservice']

    def PublicSite(self):
        return 'https://' + self.data['node']['hostname']

    def _TorUrl(self):
        return 'http://' + self.data['node']['onionservice'] + '/'

    def _HTTPSUrl(self):
        return 'https://' + self.data['node']['hostname'] + '/'

    def TorUrl(self):
        if self.data['node']['onionservice'] == '':
            return '[NOT CONFIGURED]'

        return self._TorUrl()

    def HTTPSUrl(self):
        if self.data['node']['hostname'] == '':
            return '[NOT CONFIGURED]'

        return self._HTTPSUrl()


class ContextKeyword(Keyword):
    keyword_list = context_keywords
    data_keys = ['context']

    def ContextName(self):
        return self.data['context']['name']


class ReceiverKeyword(Keyword):
    keyword_list = receiver_keywords
    data_keys = ['receiver']

    def RecipientName(self):
        return self.data['receiver']['name']


class TipKeyword(NodeKeyword, ContextKeyword, ReceiverKeyword):
    keyword_list = NodeKeyword.keyword_list + ContextKeyword.keyword_list + ReceiverKeyword.keyword_list + tip_keywords
    data_keys =  NodeKeyword.data_keys + ContextKeyword.data_keys + ReceiverKeyword.data_keys + ['tip']

    def dump_field_entry(self, output, field, entry, indent_n):
        field_type = field['type']
        if field_type == 'checkbox':
            for k, v in entry.items():
                for option in field['options']:
                    if k == option.get('id', '') and v == 'True':
                        output += indent(indent_n) + option['label'] + '\n'
        elif field_type in ['selectbox', 'multichoice']:
            for option in field['options']:
                if entry.get('value', '') == option['id']:
                    output += indent(indent_n) + option['label'] + '\n'
        elif field_type == 'date':
            output += indent(indent_n) + ISO8601_to_pretty_str(entry.get('value', '')) + '\n'
        elif field_type == 'tos':
            answer = '☑' if entry.get('value', '') == 'True' else '☐'
            output += indent(indent_n) + answer + '\n'
        elif field_type == 'fieldgroup':
            output = self.dump_fields(output, field['children'], entry, indent_n)
        else:
            output += indent_text(entry.get('value', ''), indent_n) + '\n'

        return output + '\n'

    def dump_fields(self, output, fields, answers, indent_n):
        rows = {}
        for f in fields:
            y = f['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(f)

        rows = collections.OrderedDict(sorted(rows.items()))

        for r in rows:
            rows[r] = sorted(rows[r], key=lambda k: k['x'])

        for _, row in rows.items():
            for field in row:
                if field['type'] != 'fileupload' and field['id'] in answers:
                    output += indent(indent_n) + field['label'] + '\n'
                    entries = answers[field['id']]
                    if len(entries) == 1:
                        output = self.dump_field_entry(output, field, entries[0], indent_n + 1)
                    else:
                        i = 1
                        for entry in entries:
                            output += indent(indent_n) + '#' + str(i) + '\n'
                            output = self.dump_field_entry(output, field, entry, indent_n + 2)
                            i += 1

        return output

    def dump_questionnaire_answers(self, questionnaire, answers):
        output = ''

        questionnaire = sorted(questionnaire, key=lambda k: k['presentation_order'])

        for step in questionnaire:
            output += step['label'] + '\n'
            output = self.dump_fields(output, step['children'], answers, 1) +'\n'

        return output

    def dump_messages(self, messages):
        ret = ''
        for message in messages:
            data = copy.deepcopy(self.data)
            data['type'] = 'export_message'
            data['message'] = copy.deepcopy(message)
            template = 'export_message_whistleblower' if (message['type'] == 'whistleblower') else 'export_message_recipient'
            ret += indent_text('-' * 40) + '\n'
            ret += indent_text(Templating().format_template(self.data['notification'][template], data).encode('utf-8')) + '\n\n'

        return ret

    def TipID(self):
        return self.data['tip']['id']

    def _TorUrl(self):
        return 'http://' + self.data['node']['onionservice'] + '/#/status/' + self.data['tip']['id']

    def _HTTPSUrl(self):
        return 'https://' + self.data['node']['hostname'] + '/#/status/' + self.data['tip']['id']

    def TipNum(self):
        return self.data['tip']['sequence_number']

    def TipLabel(self):
        return self.data['tip']['label']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['tip']['creation_date'])

    def SubmissionDate(self):
        return self.EventTime()

    def ExpirationDate(self):
        # is not time zone dependent, is UTC for everyone
        return ISO8601_to_day_str(self.data['tip']['expiration_date'])

    def ExpirationWatch(self):
        missing_time = ISO8601_to_datetime(self.data['tip']['expiration_date']) - datetime_now()
        missing_hours = int(divmod(missing_time.total_seconds(), 3600)[0])
        return str(missing_hours)

    def QuestionnaireAnswers(self):
        return self.dump_questionnaire_answers(self.data['tip']['questionnaire'], self.data['tip']['answers'])

    def Comments(self):
        comments = self.data.get('comments', [])
        if len(comments) == 0:
            return '{Blank}'

        ret = self.data['node']['widget_comments_title'] + ':\n'
        ret += self.dump_messages(comments) + '\n'
        return ret + '\n'

    def Messages(self):
        messages = self.data.get('messages', [])
        if len(messages) == 0:
            return '{Blank}'

        ret = self.data['node']['widget_messages_title'] + ':\n'
        ret += self.dump_messages(messages)
        return ret + '\n'


class CommentKeyword(TipKeyword):
    data_keys =  TipKeyword.data_keys + ['comment']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['comment']['creation_date'])


class MessageKeyword(TipKeyword):
    data_keys =  TipKeyword.data_keys + ['message']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['message']['creation_date'])


class FileKeyword(TipKeyword):
    keyword_list = TipKeyword.keyword_list + file_keywords
    data_keys =  TipKeyword.data_keys + ['file']

    def FileName(self):
        return self.data['file']['name']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['file']['creation_date'])

    def FileSize(self):
        return str(self.data['file']['size'])


class ExportMessageKeyword(Keyword):
    keyword_list = export_message_keywords
    data_keys =  ['message']

    def Content(self):
        return self.data['message']['content']


class ExpirationSummaryKeyword(NodeKeyword, ContextKeyword, ReceiverKeyword):
    keyword_list = NodeKeyword.keyword_list + \
                   ReceiverKeyword.keyword_list + \
                   expiration_summary_keywords

    data_keys =  NodeKeyword.data_keys + \
                 ReceiverKeyword.data_keys + \
                 ['expiring_submission_count', 'earliest_expiration_date']

    def ExpiringSubmissionCount(self):
        return str(self.data['expiring_submission_count'])

    def EarliestExpirationDate(self):
        return ISO8601_to_pretty_str(self.data['earliest_expiration_date'])

    def _TorUrl(self):
        return 'http://' + self.data['node']['onionservice'] + '/#/receiver/tips'

    def _HTTPSUrl(self):
        return 'https://' + self.data['node']['hostname'] + '/#/receiver/tips'


class AdminPGPAlertKeyword(NodeKeyword):
    keyword_list = NodeKeyword.keyword_list + admin_pgp_alert_keywords
    data_keys =  NodeKeyword.data_keys + ['users']

    def PGPKeyInfoList(self):
        ret = ''
        for r in self.data['users']:
            fingerprint = r['pgp_key_fingerprint']
            key = fingerprint[:7] if fingerprint is not None else ''

            ret += '\t%s, %s (%s)\n' % (r['name'],
                                        key,
                                        ISO8601_to_day_str(r['pgp_key_expiration']))
        return ret


class PGPAlertKeyword(NodeKeyword):
    keyword_list = NodeKeyword.keyword_list + user_pgp_alert_keywords
    data_keys =  NodeKeyword.data_keys + ['user']

    def PGPKeyInfo(self):
        fingerprint = self.data['user']['pgp_key_fingerprint']
        key = fingerprint[:7] if fingerprint is not None else ''

        return '\t0x%s (%s)' % (key, ISO8601_to_day_str(self.data['user']['pgp_key_expiration']))


class AnomalyKeyword(NodeKeyword):
    keyword_list = NodeKeyword.keyword_list + admin_anomaly_keywords
    data_keys =  NodeKeyword.data_keys + ['alert']

    def AnomalyDetailDisk(self):
        # This happens all the time anomalies are present but disk is ok
        if self.data['alert']['stress_levels']['disk_space'] == 0:
            return u''

        if self.data['alert']['stress_levels']['disk_space'] == 1:
            return self.data['notification']['admin_anomaly_disk_low']
        elif self.data['alert']['stress_levels']['disk_space'] == 2:
            return self.data['notification']['admin_anomaly_disk_medium']
        else:
            return self.data['notification']['admin_anomaly_disk_high']

    def AnomalyDetailActivities(self):
        # This happens all the time there is not anomalous traffic
        if self.data['alert']['stress_levels']['activity'] == 0:
            return u''

        return self.data['notification']['admin_anomaly_activities']

    def ActivityAlarmLevel(self):
        return '%s' % self.data['alert']['stress_levels']['activity']

    def ActivityDump(self):
        retstr = ''

        for event, count in self.data['alert']['event_matrix'].items():
            if not count:
                continue
            retstr = '%s%s%d\n%s' % (event, (25 - len(event)) * ' ', count, retstr)

        return retstr

    def FreeMemory(self):
        return '%s' % bytes_to_pretty_str(self.data['alert']['latest_measured_freespace'])

    def TotalMemory(self):
        return '%s' % bytes_to_pretty_str(self.data['alert']['latest_measured_totalspace'])


class CertificateExprKeyword(NodeKeyword):
    keyword_list = NodeKeyword.keyword_list + https_expr_keywords
    data_keys = NodeKeyword.data_keys + ['expiration_date']

    def ExpirationDate(self):
        # is not time zone dependent, is UTC for everyone
        return ISO8601_to_day_str(self.data['expiration_date'])

    def _TorUrl(self):
        return 'http://' + self.data['node']['onionservice'] + '/#/admin/network'

    def _HTTPSUrl(self):
        return 'https://' + self.data['node']['hostname'] + '/#/admin/network'


supported_template_types = {
    u'tip': TipKeyword,
    u'comment': CommentKeyword,
    u'message': MessageKeyword,
    u'file': FileKeyword,
    u'tip_expiration': TipKeyword,
    u'tip_expiration_summary': ExpirationSummaryKeyword,
    u'pgp_alert': PGPAlertKeyword,
    u'admin_pgp_alert': AdminPGPAlertKeyword,
    u'receiver_notification_limit_reached': Keyword,
    u'export_template': TipKeyword,
    u'export_message': ExportMessageKeyword,
    u'admin_anomaly': AnomalyKeyword,
    u'admin_test_static': NodeKeyword,
    u'https_certificate_expiration': CertificateExprKeyword,
}


class Templating(object):
    def format_template(self, raw_template, data):
        keyword_converter = supported_template_types[data['type']](data)
        for _ in range(3):
            count = 0

            for kw in keyword_converter.keyword_list:
                if raw_template.count(kw):
                    # if %SomeKeyword% matches, call keyword_converter.SomeKeyword function
                    variable_content = getattr(keyword_converter, kw[1:-1])()
                    raw_template = raw_template.replace(kw, variable_content)

                    count += 1

            # remobe lines with only {Blank}
            raw_template = raw_template.replace('\n{Blank}\n', '\n')

            # remove remaining $Blank% tokens
            raw_template = raw_template.replace('\n{Blank}\n', '')

            if count == 0:
                # finally!
                break

        return raw_template

    def get_mail_subject_and_body(self, data):
        subject_template = ''
        body_template = ''

        if data['type'] == 'export_template':
            # this is currently the only template not used for mail notifications
            pass
        elif data['type'] in supported_template_types:
            subject_template = data['notification'][data['type'] + '_mail_title']
            body_template = data['notification'][data['type'] + '_mail_template']
        else:
            raise NotImplementedError('This data_type (%s) is not supported' % ['data.type'])

        if data['type'] in [u'tip', u'comment', u'file', u'message', u'tip_expiration']:
            prefix = '{TipNum} '
            if data['tip']['label'] != '':
                prefix += '[{TipLabel}] '

            subject_template = prefix + subject_template

        subject = self.format_template(subject_template, data)
        body = self.format_template(body_template, data)

        return subject, body
