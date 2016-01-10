import os

from globaleaks.handlers.base import BaseHandler
from globaleaks.settings import GLSettings
from globaleaks.security import directory_traversal_check


class CSSFileHandler(BaseHandler):
    original_css_filename = 'css/styles.css'

    def get(self):
        self.set_header("Content-Type", 'text/css')

        original_css = os.path.join(GLSettings.client_path, self.original_css_filename)
        custom_css = os.path.join(GLSettings.static_path, 'custom_stylesheet.css')

        directory_traversal_check(GLSettings.client_path, original_css)
        directory_traversal_check(GLSettings.static_path, custom_css)

        self.write_file(original_css)

        if (os.path.exists(custom_css) and os.path.isfile(custom_css)):
            self.write_file(custom_css)
