from globaleaks.plugins.base import Delivery

class SCPDelivery(Delivery):

    receiver_fields = {}

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return False

    def preparation_required(self, fileinfo, admin_fields):
        return False

    def do_delivery(self, settings, file_path):
        return False
