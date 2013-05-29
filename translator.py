import os
import re
import sys
import codecs

to_be_translated_strings = []
def clean_files():
    for filename in os.listdir('pot'):
        file_path = os.path.join('pot', filename)
        with codecs.open(file_path, 'w+', 'utf-8') as f:
            f.write("""# Copyright (C) 2013 WordPress
# This file is distributed under the same license as the WordPress package.
msgid ""
msgstr ""
"Project-Id-Version: GLClient 0.2\\n"
"Report-Msgid-Bugs-To: http://github.com/globaleaks/GlobaLeaks\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
""")

def extract_strings(file_path):
    with codecs.open(file_path) as f:
        regexp = "{{\s+\"(.+?)\"\s+\|\s+translate\s+}}"
        content = ''.join(f.readlines())
        return re.findall(regexp, content, re.DOTALL)

def add_to_po_files(string):
    for filename in os.listdir('pot'):
        file_path = os.path.join('pot', filename)

        with codecs.open(file_path, 'a', 'utf-8') as f:
            f.write(u"\n#: example.py:11\n")
            f.write(u'msgid "%s"\n' % string)
            f.write(u'msgstr ""\n')

clean_files()
for dirname, dirnames, filenames in os.walk('.'):
    # print path to all filenames.
    for filename in filenames:
        if filename.endswith(".html"):
            file_path = os.path.join(dirname, filename)
            to_be_translated_strings += extract_strings(file_path)

to_be_translated_strings = set(to_be_translated_strings)
for string in to_be_translated_strings:
    print string
    add_to_po_files(string)
