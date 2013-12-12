# -*- encoding: utf-8 -*-
#
# this file contain the class converting the %KeyWords% with data.
# perhaps exists something python-stable-portable-well know, this
# class has just be written down easily and fit our needs.
#
# If you know something better, please tell to us. At the moment,
# supporter KeyWords are here documented:
# https://github.com/globaleaks/GlobaLeaks/wiki/Customization-guide#customize-notification

from globaleaks.settings import GLSetting
from globaleaks.utils.utility import log
from globaleaks.utils.utility import very_pretty_date_time

class Templating:


    def dump_file_list(self, filelist, files_n):

        info = "%s%s%s%s%s\n" % ("Filename",
                                 " "*(40-len("Filename")),
                                 "Size (Bytes)",
                                 " "*(15-len("Size (Bytes)")),
                                 "sha256")

        for i in xrange(files_n):
            length1 = 40 - len(filelist[i]['name'])
            length2 = 15 - len(str(filelist[i]['size']))
            info += "%s%s%i%s%s\n" % (filelist[i]['name'], " "*length1,
                                      filelist[i]['size'], " "*length2,
                                      filelist[i]['sha2sum'])

        return info

    def dump_submission_fields(self, fields, wb_fields):

        dumptext = u""
        for sf in fields:
            if sf['type'] != 'text':
                log.debug("Ignored dump of field %s because is not a Text" % sf['name'])
                continue

            fnl = len(sf['name'])
            # dumptext += ("="*fnl)+"\n"+sf['name']+"\n("+sf['hint']+")\n"+("="*fnl)+"\n"
            dumptext += ("="*fnl)+"\n"+sf['name']+"\n"+("="*fnl)+"\n"
            dumptext += wb_fields[ fields[0]['key'] ]+"\n\n"

        return dumptext

    def _iterkeywords(self, template, keywords):
        if isinstance(template, dict):
            partial_template = template[GLSetting.memory_copy.default_language]
        else:
            partial_template = template
            # this is wrong!

        for key, var in keywords.iteritems():
            partial_template = partial_template.replace(key, var)

        return partial_template

    def format_template(self, template, event_dicts):
        """
        TODO research on integration of http://docs.python.org/2/library/email
        """

        node_desc = event_dicts.node_info
        assert node_desc.has_key('name')
        receiver_desc = event_dicts.receiver_info
        assert receiver_desc.has_key('name')
        context_desc = event_dicts.context_info
        assert context_desc.has_key('name')

        template_keyword = {
            '%NodeName%': node_desc['name'],
            '%HiddenService%': node_desc['hidden_service'],
            '%PublicSite%': node_desc['public_site'],
            '%ReceiverName%': receiver_desc['name'],
            # context_name contains localized data, ad the moment
            # exported only with default language, because Receiver
            # can't yet configure its hown lang.
            '%ContextName%' : context_desc['name'],
            }

        supported_event_types = [ u'file', u'comment', u'encrypted_tip', u'plaintext_tip', u'zip_collection' ]
        high_level_clearance = [ u'zip_collection', u'encrypted_tip' ]
        if event_dicts.type not in supported_event_types:
            raise AssertionError("%s at the moment supported: %s is NOT " % (supported_event_types, event_dicts.type))

        tip_template_keyword = {}
        if event_dicts.type in high_level_clearance: # only crypto tip + zip files

            # GLSetting.memory_copy.default_language is ignored here
            # because the context_info is already localized
            tip_template_keyword.update({
                '%TipFields%':
                    self.dump_submission_fields(event_dicts.context_info['fields'],
                                                event_dicts.trigger_info['wb_fields'])
            })

        if event_dicts.type == u"zip_collection": # only zip files

            tip_template_keyword.update({
                '%FileList%':
                    self.dump_file_list(event_dicts.trigger_info['files'],
                                        event_dicts.trigger_info['files_number']),
                '%FilesNumber%': str(event_dicts.trigger_info['files_number']),
                '%TotalSize%': str(event_dicts.trigger_info['total_size']),
            })

        if event_dicts.type in high_level_clearance or event_dicts.type == u'plaintext_tip':

            if len(node_desc['hidden_service']):
                tip_template_keyword.update({
                    '%TipTorURL%':
                        '%s/#/status/%s' %
                        ( node_desc['hidden_service'],
                          event_dicts.trigger_info['id']),
                    })
            else:
                tip_template_keyword.update({
                    '%TipTorURL%':
                        'ADMIN, CONFIGURE YOUR HIDDEN SERVICE (Advanced configuration)!'
                })

            if not GLSetting.memory_copy.tor2web_receiver:
                tip_template_keyword.update({
                    '%TipT2WURL%': "Ask to your admin about Tor"})
                # https://github.com/globaleaks/GlobaLeaks/issues/268
            elif len(node_desc['public_site']):
                tip_template_keyword.update({
                    '%TipT2WURL%':
                        '%s/#/status/%s' %
                        ( node_desc['public_site'],
                          event_dicts.trigger_info['id'] ),
                    })
            else:
                tip_template_keyword.update({
                    '%TipT2WURL%':
                        'ADMIN, CONFIGURE YOUR PUBLIC SITE (Advanced configuration)'
                })

            tip_template_keyword.update({
                '%EventTime%':
                    very_pretty_date_time(event_dicts.trigger_info['creation_date']),
                })

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, tip_template_keyword)
            return body

        if event_dicts.type == u'comment':

            comment_template_keyword = {
                '%CommentSource%': event_dicts.trigger_info['source'],
                '%EventTime%':
                    very_pretty_date_time(event_dicts.trigger_info['creation_date']),
                }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, comment_template_keyword)
            return body

        if event_dicts.type == u'file':

            file_template_keyword = {
                '%FileName%': event_dicts.trigger_info['name'],
                '%EventTime%':
                    very_pretty_date_time(event_dicts.trigger_info['creation_date']),
                '%FileSize%': event_dicts.trigger_info['size'],
                '%FileType%': event_dicts.trigger_info['content_type'],
                }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, file_template_keyword)
            return body

        raise AssertionError("No one can access to this section of code: has to be returned before!")


