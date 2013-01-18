from globaleaks.plugins.base import Delivery

class LocalDelivery(Delivery):

    def __init__(self):
        self.plugin_name = u'Zip download'
        self.plugin_type = u'delivery'
        self.plugin_description = u"Download submitted file from the tip interface, supports of .zip and password encryption"

        self.admin_fields = {}
        self.receiver_fields = {'enable_encryption': 'bool', 'password': 'text'}

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return False

    def preparation_required(self, fileinfo, admin_fields):
        return False

    def do_delivery(self, settings, file_path):
        return False
