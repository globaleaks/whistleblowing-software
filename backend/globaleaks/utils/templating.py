# -*- encoding: utf-8 -*-
#
# this file contain the class converting the %KeyWords% with data.
# perhaps exists something python-stable-portable-well know, this
# class has just be written down easily and fit our needs.
#
# If you know something better, please tell to us. At the moment,
# supporter KeyWords are here documented:
# https://github.com/globaleaks/GlobaLeaks/wiki/Customization-guide#customize-notification

from globaleaks.settings import GLSettings
from globaleaks.utils.utility import ISO8601_to_pretty_str, ISO8601_to_day_str, \
    ISO8601_to_datetime, datetime_now


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


archive_description_keywords = [
    '%FileList%',
    '%FilesNumber%',
    '%TotalSize%'
]


admin_pgp_alert_keywords = [
    '%PGPKeyInfoList%'
]

user_pgp_alert_keywords = [
    '%PGPKeyInfo%'
]



def dump_file_list(filelist, files_n):
    info = "%s%s%s\n" % ("Filename",
                             " "*(40-len("Filename")),
                             "Size (Bytes)")

    for i in xrange(files_n):
        info += "%s%s%i\n" % (filelist[i]['name'],
                                " "*(40 - len(filelist[i]['name'])),
                                filelist[i]['size'])

    return info

class TemplateData(dict):
    pass

class Keyword(object):
    """
    This class define the base keyword list supported by all the events
    """
    keyword_list = node_keywords
    data_keys = ['node', 'context', 'receiver']

    def __init__(self, data):
       for k in self.data_keys:
           if k not in data:
               raise "ANTANI"

       self.data = data

    def NodeName(self):
        return self.data['node']['name']

    def HiddenService(self):
        return self.data['node']['hidden_service']

    def PublicSite(self):
        return self.data['node']['public_site']


class TipKeyword(Keyword):
    keyword_list = Keyword.keyword_list + tip_keywords
    data_keys =  ['node', 'context', 'receiver', 'tip']

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
        return "[%s-%d] " % ((ISO8601_to_datetime(self.data['tip']['creation_date'])).strftime("%Y%m%d"), self.data['tip']['progressive'])

    def TipLabel(self):
        return "[" + self.data['tip']['label'] + "] " if self.data['tip']['label'] != '' else ""

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['tip']['creation_date'], float(self.data['receiver']['timezone']))

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
    data_keys =  ['node', 'context', 'receiver', 'tip', 'comment']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['comment']['creation_date'], float(self.data['receiver']['timezone']))


class MessageKeyword(TipKeyword):
    data_keys =  ['node', 'context', 'receiver', 'tip', 'message']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['message']['creation_date'], float(self.data['receiver']['timezone']))


class FileKeyword(TipKeyword):
    keyword_list = TipKeyword.keyword_list + file_keywords
    data_keys =  ['node', 'context', 'receiver', 'tip', 'file']

    def FileName(self):
        return self.data['file']['name']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.data['file']['creation_date'], float(self.data['receiver']['timezone']))

    def FileSize(self):
        return self.data['file']['size']

    def FileType(self):
        return self.data['file']['content_type']


class ArchiveDescription(TipKeyword):
    keyword_list = TipKeyword.keyword_list + archive_description_keywords
    data_keys =  ['node', 'context', 'receiver', 'tip', 'archive_description']

    def FileList(self):
        return dump_file_list(self.data['archive']['files'], self.data['archive']['file_counter'])

    def FilesNumber(self):
        return str(self.data['archive']['file_counter'])

    def TotalSize(self):
        return str(self.data['archive']['total_size'])


class AdminPGPAlertKeyword(Keyword):
    keyword_list = node_keywords + admin_pgp_alert_keywords
    data_keys =  ['node', 'users']

    def PGPKeyInfoList(self):
        ret = ""
        for r in self.data['users']:
            fingerprint = r['pgp_key_fingerprint']
            if fingerprint is not None:
                key = fingerprint[:7]
            else:
                key = ""

            ret += "\t%s, %s (%s)\n" % (r['name'],
                                        key,
                                        ISO8601_to_day_str(r['pgp_key_expiration']))
        return ret


class PGPAlertKeyword(Keyword):
    keyword_list = node_keywords + user_pgp_alert_keywords
    data_keys =  ['node', 'user']

    def PGPKeyInfo(self):
        fingerprint = self.data['user']['pgp_key_fingerprint']
        if fingerprint is not None:
            key = fingerprint[:7]
        else:
            key = ""

        return "\t0x%s (%s)" % (key, ISO8601_to_day_str(self.data['user']['pgp_key_expiration']))


supported_template_types = {
    u'tip': TipKeyword,
    u'comment': CommentKeyword,
    u'message': MessageKeyword,
    u'file': FileKeyword,
    u'tip_expiration': TipKeyword,
    u'pgp_expiration_alert': PGPAlertKeyword,
    u'admin_pgp_expiration_alert': AdminPGPAlertKeyword,
    u'receiver_notification_limit_reached': Keyword,
    u'archive_description': ArchiveDescription
}


class Templating(object):
    def format_template(self, raw_template, data):
        # For each Event type, we've to dispatch the right Keyword class
        keyword_converter = supported_template_types[data['type']](data)

        # we've now:
        # 1) template => directly from Notification.*_template
        # 2) keyword_converter => object aligned with Event type and data

        for kw in keyword_converter.keyword_list:
            if raw_template.count(kw):
                # if %SomeKeyword% matches, call keyword_converter.SomeKeyword function
                variable_content = getattr(keyword_converter, kw[1:-1])()
                raw_template = raw_template.replace(kw, variable_content)

        return raw_template

    def get_mail_subject_and_body(self, data):
        def replace_variables(template, data):
            return Templating().format_template(template, data)

        if data['type'] in [u'tip', u'comment', u'message', u'file', u'tip_expiration', 'receiver_notification_limit_reached']:
            subject_template = data['notification'][data['type'] + '_mail_title']
            body_template = data['notification'][data['type'] + '_mail_template']
        else:
            raise NotImplementedError("This data_type (%s) is not supported" % ['data.type'])

        if data['type'] in [u'tip', u'comment', u'file', u'message', u'tip_expiration']:
            subject_template = "%TipNum%%TipLabel%" + subject_template

        subject = self.format_template(subject_template, data)
        body = self.format_template(body_template, data)

        return subject, body
