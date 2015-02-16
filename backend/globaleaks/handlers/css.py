import os

from globaleaks.handlers.base import BaseHandler
from globaleaks.settings import GLSetting

class LTRCSSFileHandler(BaseHandler):
    original_css_filename = 'styles.css'

    def get(self):
       self.set_header("Content-Type", 'text/css')

       original_css = os.path.join(GLSetting.glclient_path, self.original_css_filename)
       custom_css = os.path.join(GLSetting.static_path, 'custom_stylesheet.css')

       self.write_file(original_css)
       self.write_file(custom_css)

class RTLCSSFileHandler(LTRCSSFileHandler):
     original_css_filename = 'styles-rtl.css'
