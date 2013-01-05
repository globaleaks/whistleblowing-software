from globaleaks.utils import log, gltime
from globaleaks.plugins.base import FileProcess

class TypeValidation(FileProcess):

    def __init__(self):
        self.plugin_name = 'type_validation'
        self.plugin_type = 'delivery'
        self.plugin_description = "Validate file type"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'TypeList' : 'text' }
        self.receiver_fields = None


    def validate_admin_opt(self, admin_fields):
        return True

    def do_fileprocess(self, filepath, admin_fields):
        return False


