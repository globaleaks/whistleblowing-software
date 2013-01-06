from globaleaks.utils import log, gltime
from globaleaks.plugins.base import FileProcess

class Virustotal(FileProcess):

    def __init__(self):
        self.plugin_name = u'VirusTotal'
        self.plugin_type = u'fileprocess'
        self.plugin_description = "Submit a file to VirusTotal in order to detect malware presence"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'TODO' : 'text' }

    def validate_admin_opt(self, admin_fields):
        return True

    def do_fileprocess(self, filepath, admin_fields):
        return False
