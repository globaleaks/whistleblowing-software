# -*- encoding: utf-8 -*-
#
# this file contain the class converting the %KeyWords% with data.
# perhaps exists something python-stable-portable-well know, this
# class has just be written down easily and fit our needs.
#
# If you know something better, please tell to us. At the moment,
# supporter KeyWords are here documented:
# https://github.com/globaleaks/GlobaLeaks/wiki/Customization-guide#customize-notification

import copy

from globaleaks import models
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import ISO8601_to_pretty_str, ISO8601_to_day_str, \
    ISO8601_to_datetime, datetime_now, bytes_to_pretty_str

node_keywords = [
    '%NodeName%',
    '%HiddenService%',
    '%PublicSite%',
]


tip_keywords = [
    '%TipID%',
    '%TipTorURL%',
    '%TipT2WURL%',
    '%TorURL%',
    '%T2WURL%',
    '%TipNum%',
    '%TipLabel%',
    '%EventTime%',
    '%SubmissionDate%',
    '%ExpirationDate%',
    '%ExpirationWatch%',
    '%RecipientName%',
    '%ContextName%'
]

file_keywords = [
    '%FileName%',
    '%FileSize%',
    '%FileType%'
]

export_template_keywords = [
    '%Comments%',
    '%Messages%',
    '%FileList%',
]

export_message_keywords = [
    '%Content%'
]

admin_pgp_alert_keywords = [
    '%PGPKeyInfoList%'
]

user_pgp_alert_keywords = [
    '%PGPKeyInfo%'
]

admin_anomaly_keywords = [
    "%AnomalyDetailDisk%",
    "%AnomalyDetailActivities%",
    "%ActivityAlarmLevel%",
    "%ActivityDump%",
    "%NodeName%",
    "%FreeMemory%",
    "%TotalMemory%"
]


def indent(n=1):
    return "  " * n


def indent_text(text, n=1):
    return '\n'.join(['  ' * n + l for l in text.splitlines()])


def dump_field_entry(output, field, entry, indent_n):
    field_type = field["type"]
    if field_type == "checkbox":
        for v, k in entry.iteritems():
            for option in field["options"]:
                if k == option.id and v == "True":
                    output += indent(indent_n) + option["label"] + "\n"
    elif field_type in ["selectbox", "multichoice"]:
        for option in field["options"]:
            if entry["value"] == option.id:
                output += indent(indent_n) + option["label"] + "\n"
    elif field_type == "date":
        output += indent(indent_n) + entry["value"] # FIXME: format date
    elif field_type == "tos":
        if entry["value"] == "True":
            output += indent(indent_n) + "\u2713" + "\n"
    elif field_type == "fieldgroup":
        output = dump_fields(output, field["children"], entry, indent_n)
    else:
        output += indent(indent_n) + entry["value"] + "\n"

    output += "\n"

    return output


def dump_fields(output, fields, answers, indent_n):
    for field in fields:
        if field["type"] != "fileupload" and field["id"] in answers:
            output += indent(indent_n) + field["label"] + "\n"
            entries = answers[field["id"]]
            if len(entries) == 1:
                output = dump_field_entry(output, field, entries[0], indent_n + 1)
            else:
                i = 1
                for entry in entries:
                    output += indent(intent_n) + "#" + str(i) + "\n"
                    output = dump_field_entry(output, field, entry, indent_n + 2)
                    i += 1

    return output


def dump_questionnaire_answers(questionnaire, answers):
    output = ""
    for step in questionnaire:
        output += step["label"] + "\n"
        output = dump_fields(output, step["children"], answers, 1)
        output += "\n"

    return output


def dump_file_list(file_list):
    info = "%s%s%s\n" % ("Filename",
                             " "*(40-len("Filename")),
                             "Size (Bytes)")

    for i in xrange(len(file_list)):
        info += "%s%s%i\n" % (file_list[i]["name"],
                              " "*(40 - len(file_list[i]["name"])),
                              file_list[i]["size"])

    return info


class Keyword(object):
    """
    This class define the base keyword list supported by all the events
    """
    keyword_list = node_keywords
    data_keys = ['node', 'notification']

    def __init__(self, data):
        # node and notification are always injected as they contain general information
        for k in self.data_keys:
            if k not in data:
                raise errors.InternalServerError("Missing key '%s' while resolving template '%s'" % (k, type(self).__name__))

        self.data = data

    def NodeName(self):
        return self.data['node']['name']

    def HiddenService(self):
        return self.data['node']['hidden_service']

    def PublicSite(self):
        return self.data['node']['public_site']


class TipKeyword(Keyword):
    keyword_list = Keyword.keyword_list + tip_keywords
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip']

    def TipID(self):
        return self.data['tip']['id']

    def TipTorURL(self):
        hidden_service = self.data['node']['hidden_service']

        if len(hidden_service):
            retstr = '%s/#/status/%s' % (hidden_service, self.data['tip']['id'])
        else:
            retstr = '[NOT CONFIGURED]'

        return retstr

    def TipT2WURL(self):
        public_site = self.data['node']['public_site']

        if not GLSettings.memory_copy.tor2web_access['receiver']:
            retstr = "DISABLED"
        elif len(public_site):
            retstr =  '%s/#/status/%s' % (public_site, self.data['tip']['id'])
        else:
            retstr = '[NOT CONFIGURED]'

        return retstr

    def TorURL(self):
        return self.TipTorURL()

    def T2WURL(self):
        return self.TipT2WURL()

    def TipNum(self):
        return self.data['tip']['sequence_number']

    def TipLabel(self):
        return "[" + self.data['tip']['label'] + "] " if self.data['tip']['label'] != '' else ""

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['tip']['creation_date'], float(self.data['receiver']['timezone']))

    def SubmissionDate(self):
        return self.EventTime()

    def ExpirationDate(self):
        # is not time zone dependent, is UTC for everyone
        return ISO8601_to_day_str(self.data['tip']['expiration_date'], float(self.data['receiver']['timezone']))

    def ExpirationWatch(self):
        missing_time = ISO8601_to_datetime(self.data['tip']['expiration_date']) - datetime_now()
        missing_hours = int(divmod(missing_time.total_seconds(), 3600)[0])
        return str(missing_hours)

    def ContextName(self):
        return self.data['context']['name']

    def RecipientName(self):
        return self.data['receiver']['name']


class CommentKeyword(TipKeyword):
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip', 'comment']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['comment']['creation_date'], float(self.data['receiver']['timezone']))


class MessageKeyword(TipKeyword):
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip', 'message']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['message']['creation_date'], float(self.data['receiver']['timezone']))


class FileKeyword(TipKeyword):
    keyword_list = TipKeyword.keyword_list + file_keywords
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip', 'file']

    def FileName(self):
        return self.data['file']['name']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['file']['creation_date'], float(self.data['receiver']['timezone']))

    def FileSize(self):
        return str(self.data['file']['size'])

    def FileType(self):
        return self.data['file']['content_type']


class ExportKeyword(TipKeyword):
    keyword_list = TipKeyword.keyword_list + export_template_keywords
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip', 'comments', 'messages', 'files']

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

    def Comments(self):
        ret = self.data['node']['widget_comments_title'] + ':\n'
        ret += self.dump_messages(self.data['comments'])
        return ret

    def Messages(self):
        ret = self.data['node']['widget_messages_title'] + ':\n'
        ret += self.dump_messages(self.data['messages'])
        return ret

    def FileList(self):
        return dump_file_list(self.data['files'])


class ExportMessageKeyword(TipKeyword):
    keyword_list = TipKeyword.keyword_list + export_template_keywords + export_message_keywords
    data_keys =  ['node', 'notification', 'context', 'receiver', 'tip', 'message']

    def Content(self):
        return self.data['message']['content']


class AdminPGPAlertKeyword(Keyword):
    keyword_list = Keyword.keyword_list + admin_pgp_alert_keywords
    data_keys =  ['node', 'notification', 'users']

    def PGPKeyInfoList(self):
        ret = ""
        for r in self.data['users']:
            fingerprint = r['pgp_key_fingerprint']
            key = fingerprint[:7] if fingerprint is not None else ""

            ret += "\t%s, %s (%s)\n" % (r['name'],
                                        key,
                                        ISO8601_to_day_str(r['pgp_key_expiration']))
        return ret


class PGPAlertKeyword(Keyword):
    keyword_list = Keyword.keyword_list + user_pgp_alert_keywords
    data_keys =  ['node', 'notification', 'user']

    def PGPKeyInfo(self):
        fingerprint = self.data['user']['pgp_key_fingerprint']
        key = fingerprint[:7] if fingerprint is not None else ""

        return "\t0x%s (%s)" % (key, ISO8601_to_day_str(self.data['user']['pgp_key_expiration']))


class AnomalyKeyword(Keyword):
    keyword_list = Keyword.keyword_list + admin_anomaly_keywords
    data_keys =  ['node', 'notification', 'alert']

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
        return "%s" % self.data['alert']['stress_levels']['activity']

    def ActivityDump(self):
        retstr = ""

        for event, amount in self.data['alert']['event_matrix'].iteritems():
            if not amount:
                continue
            retstr = "%s%s%d\n%s" % (event, (25 - len(event)) * " ", amount, retstr)

        return retstr

    def FreeMemory(self):
        return "%s" % bytes_to_pretty_str(self.data['alert']['latest_measured_freespace'])

    def TotalMemory(self):
        return "%s" % bytes_to_pretty_str(self.data['alert']['latest_measured_totalspace'])


supported_template_types = {
    u'tip': TipKeyword,
    u'comment': CommentKeyword,
    u'message': MessageKeyword,
    u'file': FileKeyword,
    u'tip_expiration': TipKeyword,
    u'pgp_alert': PGPAlertKeyword,
    u'admin_pgp_alert': AdminPGPAlertKeyword,
    u'receiver_notification_limit_reached': Keyword,
    u'export_template': ExportKeyword,
    u'export_message': ExportMessageKeyword,
    u'admin_anomaly': AnomalyKeyword
}


class Templating(object):
    def format_template(self, raw_template, data):
        keyword_converter = supported_template_types[data['type']](data)
        iterations = 3
        stop = False
        while (stop is False and iterations > 0):
            iterations -= 1
            count = 0

            for kw in keyword_converter.keyword_list:
                if raw_template.count(kw):
                    # if %SomeKeyword% matches, call keyword_converter.SomeKeyword function
                    variable_content = getattr(keyword_converter, kw[1:-1])()
                    raw_template = raw_template.replace(kw, variable_content)

                    count += 1

            # remobe lines with only %Blank%
            raw_template = raw_template.replace('\n%Blank%\n', '\n')

            # remove remaining $Blank% tokens
            raw_template = raw_template.replace('\n%Blank%\n', '')

            if count == 0:
                # finally!
                stop = True
                break

        return raw_template

    def get_mail_subject_and_body(self, data):
        if data['type'] == 'export_template':
            # this is currently the only template not used for mail notifications
            pass
        elif data['type'] in supported_template_types:
            subject_template = data['notification'][data['type'] + '_mail_title']
            body_template = data['notification'][data['type'] + '_mail_template']
        else:
            raise NotImplementedError("This data_type (%s) is not supported" % ['data.type'])

        if data['type'] in [u'tip', u'comment', u'file', u'message', u'tip_expiration']:
            subject_template = "%TipNum% %TipLabel% " + subject_template

        subject = self.format_template(subject_template, data)
        body = self.format_template(body_template, data)

        return subject, body

    def db_prepare_mail(self, store, data):
        subject, body = self.get_mail_subject_and_body(data)

        mail = models.Mail({
            'address': data['address'],
            'subject': subject,
            'body': body
        })

