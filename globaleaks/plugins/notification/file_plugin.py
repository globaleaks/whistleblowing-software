from globaleaks.utils import log
from globaleaks.plugins.base import Notification

class FileNotification(Notification):

    def __init__(self):
        self.plugin_name = u'File'
        self.plugin_type = u'notification'
        self.plugin_description = u"Dummy notification system, copy the received file in a directory"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'directory' : 'text' }
        self.receiver_fields = {'filename' : 'text'}

    def initialize(self, admin_fields):
        return True

    def validate_admin_opt(self, admin_fields):
        return True

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return True

    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, settings, data_type, data):

        af = settings['admin_settings']
        rf = settings['receiver_settings']

        filepath = "%s/%s" % (af['directory'], rf['filename'])
        print "file/do_notifiy is opening: ", filepath

        return True
