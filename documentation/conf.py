# -*- coding: utf-8 -*-
#
# GlobaLeaks documentation build configuration file, created by
# sphinx-quickstart on Thu Jul  6 16:34:48 2017.
#
import os
import sys

sys.path.insert(0, os.path.abspath('../backend'))

autodoc_member_order = 'bysource'
autodoc_default_flags = ['members', 'show-inheritance', 'undoc-members']

extensions = [
  'sphinx_rtd_theme'
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

from globaleaks import __author__,  __copyright__, __version__
project = __author__
copyright = __copyright__
author = __author__
version = __version__
release = __version__


language = 'en'
exclude_patterns = ['_build']
show_authors = False
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
html_logo = 'logo-html.png'
html_favicon = '../client/app/data/favicon.ico'
html_show_copyright = False
htmlhelp_basename = 'globaleaks'

latex_elements = {
  'sphinxsetup': 'TitleColor={HTML}{377abc}, \
                  InnerLinkColor={HTML}{377abc}, \
                  OuterLinkColor={HTML}{377abc}',
}

latex_documents = [
    (master_doc, 'GlobaLeaks.tex', u'Documentation', '', 'manual'),
]

latex_logo = 'logo-latex.png'

man_pages = [
    (master_doc, 'globaleaks', u'GlobaLeaks Documentation',
     [author], 1)
]

texinfo_documents = [
    (master_doc, 'GlobaLeaks', u'GlobaLeaks Documentation',
     author, 'GlobaLeaks', ' GlobaLeaks is free, open souce software enabling anyone to easily set up and maintain a secure whistleblowing platform',
     'Miscellaneous'),
]

html_theme_options = {
  'style_nav_header_background': '#377abc',
}

def setup(app):
    app.add_css_file("custom.css")
