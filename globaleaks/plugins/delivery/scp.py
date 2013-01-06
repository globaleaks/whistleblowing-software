from globaleaks.plugins.base import Delivery

class SCPDelivery(Delivery):

    def __init__(self):
        self.plugin_name = u'secure copy'
        self.plugin_type = u'delivery'
        self.plugin_description = u"Perform a secure copy (ssh) of the submitted files"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {}
        self.receiver_fields = {'Server': 'text', 'Port' : 'int', 'username' : 'text', 'password': 'text' }

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return False

    def preparation_required(self, fileinfo, admin_fields):
        return False

    def do_delivery(self, settings, file_path):
        return False
