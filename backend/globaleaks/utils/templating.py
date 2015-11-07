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

def dump_file_list(filelist, files_n):
    info = "%s%s%s\n" % ("Filename",
                             " "*(40-len("Filename")),
                             "Size (Bytes)")

    for i in xrange(files_n):
        info += "%s%s%i\n" % (filelist[i]['name'],
                                " "*(40 - len(filelist[i]['name'])),
                                filelist[i]['size'])

    return info

class Keyword(object):
    """
    This class define the base keyword list supported by all the events,
    in example, %NodeName% is a keyword always available. Other keywords can
    be used only in specific Event.
    """

    shared_keywords = [
        '%NodeName%',
        '%HiddenService%',
        '%PublicSite%',
        '%RecipientName%',
        '%ContextName%',
        '%NodeSignature%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc):

        self.keyword_list = Keyword.shared_keywords

        self.node = node_desc
        self.context = context_desc
        self.receiver = receiver_desc

    def NodeName(self):
        return self.node['name']

    def HiddenService(self):
        return self.node['hidden_service']

    def PublicSite(self):
        return self.node['public_site']

    def RecipientName(self):
        return self.receiver['name']

    def ContextName(self):
        return self.context['name']

    def NodeSignature(self):
        # FIXME currently the NodeSignature is mapped on node name;
        # in future we could evaluate to introduce a different
        # variable to permit better customizations.
        return self.node['name']

class TipKeyword(Keyword):
    tip_keywords = [
        '%TipTorURL%',
        '%TipT2WURL%',
        '%TorURL%',
        '%T2WURL%',
        '%TipNum%',
        '%TipLabel%',
        '%EventTime%',
        '%ExpirationDate%',
        '%ExpirationWatch%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, *x):

        super(TipKeyword, self).__init__(node_desc, context_desc,
                                         receiver_desc)

        self.keyword_list += TipKeyword.tip_keywords
        self.tip = tip_desc

    def TipTorURL(self):
        if len(self.node['hidden_service']):
            retstr = '%s/#/status/%s' % (self.node['hidden_service'], self.tip['id'])
        else:
            retstr = '[NOT CONFIGURED]'
        return retstr

    def TipT2WURL(self):
        """
        we shall enhance this issue:
        https://github.com/globaleaks/GlobaLeaks/issues/268
        making that if one of these function return None, the entire line is stripped.
        This can avoid the awkward effect of 'Public Url: [Ask to your admin about Tor]'
        """
        if not GLSettings.memory_copy.tor2web_access['receiver']:
            retstr = "DISABLED"
        elif len(self.node['public_site']):
            retstr =  '%s/#/status/%s' % ( self.node['public_site'], self.tip['id'] )
        else:
            retstr = 'ADMIN, CONFIGURE YOUR PUBLIC SITE (Advanced configuration)!'

        return retstr

    def TorURL(self):
        return self.TipTorURL()

    def T2WURL(self):
        return self.TipT2WURL()

    def TipNum(self):
        return "[%s-%d] " % ((ISO8601_to_datetime(self.tip['creation_date'])).strftime("%Y%m%d"), self.tip['progressive'])

    def TipLabel(self):
        return "[" + self.tip['label'] + "] " if self.tip['label'] != '' else ""

    def EventTime(self):
        return ISO8601_to_pretty_str(self.tip['creation_date'], float(self.receiver['timezone']))

    def ExpirationDate(self):
        # is not time zone dependent, is UTC for everyone
        return ISO8601_to_day_str(self.tip['expiration_date'], float(self.receiver['timezone']))

    def ExpirationWatch(self):
        missing_time = ISO8601_to_datetime(self.tip['expiration_date']) - datetime_now()
        missing_hours = int(divmod(missing_time.total_seconds(), 3600)[0])
        return unicode(missing_hours)

class CommentKeyword(TipKeyword):
    comment_keywords = [
        '%CommentSource%',
        '%EventTime%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, comment_desc):
        super(CommentKeyword, self).__init__(node_desc, context_desc, receiver_desc, tip_desc)

        self.keyword_list += CommentKeyword.comment_keywords
        self.comment = comment_desc

    def CommentSource(self):
        return self.comment['type']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.comment['creation_date'], float(self.receiver['timezone']))


class MessageKeyword(TipKeyword):
    message_keywords = [
        '%MessageSource%',
        '%EventTime%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, message_desc):
        super(MessageKeyword, self).__init__(node_desc, context_desc,
                                             receiver_desc,
                                             tip_desc)

        self.keyword_list += MessageKeyword.message_keywords
        self.message = message_desc

    def MessageSource(self):
        return self.message['author']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.message['creation_date'], float(self.receiver['timezone']))


class FileKeyword(TipKeyword):
    file_keywords = [
        '%FileName%',
        '%EventTime%',
        '%FileSize%',
        '%FileType%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, file_desc):
        super(FileKeyword, self).__init__(node_desc, context_desc,
                                          receiver_desc,
                                          tip_desc)

        self.keyword_list += FileKeyword.file_keywords
        self.file = file_desc

    def FileName(self):
        return self.file['name']

    def EventTime(self):
        return ISO8601_to_pretty_str(self.file['creation_date'], float(self.receiver['timezone']))

    def FileSize(self):
        return self.file['size']

    def FileType(self):
        return self.file['content_type']


class ZipFileKeyword(TipKeyword):
    zip_file_keywords = [
        '%FileList%',
        '%FilesNumber%',
        '%TotalSize%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, zip_desc):
        super(ZipFileKeyword, self).__init__(node_desc, context_desc,
                                             receiver_desc,
                                             tip_desc)

        self.keyword_list += ZipFileKeyword.zip_file_keywords
        self.zip = zip_desc

    def FileList(self):
        return dump_file_list(self.zip['files'], self.zip['file_counter'])

    def FilesNumber(self):
        return str(self.zip['file_counter'])

    def TotalSize(self):
        return str(self.zip['total_size'])


class PingMailKeyword(Keyword):
    ping_mail_keywords = [
        '%RecipientName%',
        '%EventCount%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, ping_desc):
        """
        This is a reduced version because PingMail are
        thinked to have least information as possible
        """
        super(PingMailKeyword, self).__init__(node_desc, context_desc, receiver_desc)

        self.keyword_list += PingMailKeyword.ping_mail_keywords

        self.name = receiver_desc['name']
        self.counter = ping_desc['counter']

    def RecipientName(self):
        return str(self.name)

    def EventCount(self):
        return str(self.counter)


class AdminPGPAlertKeyword(Keyword):
    admin_pgp_alert_keywords = [
        "%PGPKeyInfoList%"
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, alert_desc):
        super(AdminPGPAlertKeyword, self).__init__(node_desc, context_desc, receiver_desc)

        self.keyword_list += AdminPGPAlertKeyword.admin_pgp_alert_keywords

        self.alert = alert_desc

    def PGPKeyInfoList(self):
        ret = ""
        for r in self.alert['expired_or_expiring']:
            if r['pgp_key_fingerprint']:
                key = r['pgp_key_fingerprint'][:7]
            else:
                key = ""

            ret += "\t%s, %s (%s)\n" % (r['name'],
                                    key,
                                    ISO8601_to_day_str(r['pgp_key_expiration']))
        return ret


class PGPAlertKeyword(Keyword):
    pgp_alert_keywords = [
        "%PGPKeyInfo%"
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, *x):
        super(PGPAlertKeyword, self).__init__(node_desc, context_desc, receiver_desc)

        self.keyword_list += PGPAlertKeyword.pgp_alert_keywords

    def PGPKeyInfo(self):
        if self.receiver['pgp_key_fingerprint']:
            key = self.receiver['pgp_key_fingerprint'][:7]
        else:
            key = ""

        return "\t0x%s (%s)" % (key, ISO8601_to_day_str(self.receiver['pgp_key_expiration']))

class ReceiverKeyword(Keyword):
    """
    At the moment is pretty the same of _Keyword, but require a
    dedicated __init__ because the params are screw up otherwise,
    but quite likely, is time to think some notification with more
    Receiver information: this will be the template.
    """
    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, *x):
        super(ReceiverKeyword, self).__init__(node_desc, context_desc, receiver_desc)


class Templating(object):
    supported_event_types = {
        u'tip': TipKeyword,
        u'file': FileKeyword,
        u'comment': CommentKeyword,
        u'message': MessageKeyword,
        u'zip_collection': ZipFileKeyword,
        u'ping_mail': PingMailKeyword,
        u'admin_pgp_expiration_alert': AdminPGPAlertKeyword,
        u'pgp_expiration_alert': PGPAlertKeyword,
        u'tip_expiration': TipKeyword,
        u'receiver_notification_limit_reached': ReceiverKeyword
    }

    def format_template(self, raw_template, event_dicts):
        if event_dicts.type not in self.supported_event_types.keys():
            raise AssertionError("%s at the moment supported: [%s] is NOT " %
                                 (self.supported_event_types.keys(), event_dicts.type))

        # For each Event type, we've to dispatch the right Keyword class
        TemplateClass = self.supported_event_types[event_dicts.type]
        keyword_converter = TemplateClass(event_dicts.node_info, event_dicts.context_info,
                                          event_dicts.receiver_info, event_dicts.tip_info,
                                          event_dicts.subevent_info)

        # we've now:
        # 1) template => directly from Notification.*_template
        # 2) keyword_converter => object aligned with Event type and data

        for kw in keyword_converter.keyword_list:
            if raw_template.count(kw):
                # if %SomeKeyword% matches, call keyword_converter.SomeKeyword function
                variable_content = getattr(keyword_converter, kw[1:-1])()
                raw_template = raw_template.replace(kw, variable_content)

        # Is no more Raw, because all the keywords that shall be converted in
        # the Event.type, has been converted. So if you have request %TipFields% in
        # a Comment notification template, you would get just a message with a not
        # converted keyword.
        return raw_template
