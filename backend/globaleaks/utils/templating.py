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
        return self.node.get('name', '')

    def HiddenService(self):
        return self.node.get('hidden_service', '')

    def PublicSite(self):
        return self.node.get('public_site', '')

    def RecipientName(self):
        return self.receiver.get('name', '')

    def ContextName(self):
        return self.context.get('name', '')

    def NodeSignature(self):
        # FIXME currently the NodeSignature is mapped on node name;
        # in future we could evaluate to introduce a different
        # variable to permit better customizations.
        return self.node.get('name', '')

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
        if len(self.node.get('hidden_service', '')):
            retstr = '%s/#/status/%s' % (self.node.get('hidden_service', ''), self.tip.get('id'))
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
        elif len(self.node.get('public_site', '')):
            retstr =  '%s/#/status/%s' % ( self.node.get('public_site', ''), self.tip.get('id', ''))
        else:
            retstr = 'ADMIN, CONFIGURE YOUR PUBLIC SITE (Advanced configuration)!'

        return retstr

    def TorURL(self):
        return self.TipTorURL()

    def T2WURL(self):
        return self.TipT2WURL()

    def TipNum(self):
        return "[%s-%d] " % ((ISO8601_to_datetime(self.tip.get('creation_date', ''))).strftime("%Y%m%d"), self.tip.get('progressive', ''))

    def TipLabel(self):
        return "[" + self.tip.get('label', '') + "] " if self.tip.get('label', '') != '' else ""

    def EventTime(self):
        return ISO8601_to_pretty_str(self.tip.get('creation_date', ''), float(self.receiver.get('timezone', 0)))

    def ExpirationDate(self):
        # is not time zone dependent, is UTC for everyone
        return ISO8601_to_day_str(self.tip.get('expiration_date', ''), float(self.receiver.get('timezone', '')))

    def ExpirationWatch(self):
        missing_time = ISO8601_to_datetime(self.tip.get('expiration_date')) - datetime_now()
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
        return ISO8601_to_pretty_str(self.comment.get('creation_date', ''), float(self.receiver.get('timezone', 0)))


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
        return self.message.get('author', '')

    def EventTime(self):
        return ISO8601_to_pretty_str(self.message.get('creation_date', ''), float(self.receiver.get('timezone', 0)))


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
        return self.file.get('name', '')

    def EventTime(self):
        return ISO8601_to_pretty_str(self.file.get('creation_date', ''), float(self.receiver.get('timezone', 0)))

    def FileSize(self):
        return self.file.get('size', 0)

    def FileType(self):
        return self.file.get('content_type', '')


class ArchiveDescription(TipKeyword):
    archive_description_keywords = [
        '%FileList%',
        '%FilesNumber%',
        '%TotalSize%'
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, archive_desc):
        super(ArchiveDescription, self).__init__(node_desc, context_desc,
                                             receiver_desc,
                                             tip_desc)

        self.keyword_list += ArchiveDescription.archive_description_keywords
        self.archive = archive_desc

    def FileList(self):
        return dump_file_list(self.archive.get('files', []), self.archive.get('file_counter', 0))

    def FilesNumber(self):
        return str(self.archive.get('file_counter', 0))

    def TotalSize(self):
        return str(self.archive.get('total_size', 0))


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

        self.name = receiver_desc.get('name', '')
        self.counter = ping_desc.get('counter', 0)

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
        for r in self.alert.get('expired_or_expiring', []):
            fingerprint = r.get('pgp_key_fingerprint', None)
            if fingerprint is not None:
                key = fingerprint[:7]
            else:
                key = ""

            ret += "\t%s, %s (%s)\n" % (r.get('name', ''),
                                        key,
                                        ISO8601_to_day_str(r.get('pgp_key_expiration', '')))
        return ret


class PGPAlertKeyword(Keyword):
    pgp_alert_keywords = [
        "%PGPKeyInfo%"
    ]

    def __init__(self, node_desc, context_desc, receiver_desc, tip_desc, *x):
        super(PGPAlertKeyword, self).__init__(node_desc, context_desc, receiver_desc)

        self.keyword_list += PGPAlertKeyword.pgp_alert_keywords

    def PGPKeyInfo(self):
        fingerprint = self.receiver.get('pgp_key_fingerprint', None)
        if fingerprint is not None:
            key = fingerprint[:7]
        else:
            key = ""

        return "\t0x%s (%s)" % (key,
                                ISO8601_to_day_str(self.receiver.get('pgp_key_expiration', '')))


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
        u'archive_description': ArchiveDescription,
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
