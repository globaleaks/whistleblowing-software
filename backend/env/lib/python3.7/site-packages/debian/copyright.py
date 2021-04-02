"""Utilities for parsing and creating machine-readable debian/copyright files.

The specification for the format (also known as DEP5) is available here:
https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/

Start from the Copyright docstring for usage information.

Copyright Classes
-----------------
"""

# Copyright (C) 2014       Google, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import unicode_literals

import collections
import itertools
import io
import re
import warnings

try:
    # pylint: disable=unused-import
    from typing import (
        Any,
        IO,
        Iterable,
        Iterator,
        List,
        Optional,
        Pattern,
        Text,
        Tuple,
        Union,
    )
except ImportError:
    # Lack of typing is not important at runtime
    pass

from debian import deb822


_CURRENT_FORMAT = (
    'https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/')

_KNOWN_FORMATS = frozenset([
    _CURRENT_FORMAT,
])


class Error(Exception):
    """Base class for exceptions in this module."""


class NotMachineReadableError(Error):
    """Raised when the input is not a machine-readable debian/copyright file."""


class MachineReadableFormatError(Error, ValueError):
    """Raised when the input is not valid.

    This is both a `copyright.Error` and a `ValueError` to ease handling of
    errors coming from this module.
    """


def _complain(msg, strict):
    # type: (str, bool) -> None
    if strict:
        raise MachineReadableFormatError(msg)
    warnings.warn(msg)


class Copyright(object):
    """Represents a debian/copyright file.

    A Copyright object contains a Header paragraph and a list of additional
    Files or License paragraphs.  It provides methods to iterate over those
    paragraphs, in addition to adding new ones.  It also provides a mechanism
    for finding the Files paragraph (if any) that matches a particular
    filename.

    Typical usage::

        with io.open('debian/copyright', 'rt', encoding='utf-8') as f:
            c = copyright.Copyright(f)

            header = c.header
            # Header exposes standard fields, e.g.
            print('Upstream name: ', header.upstream_name)
            lic = header.license
            if lic:
                print('Overall license: ', lic.synopsis)
            # You can also retrive and set custom fields.
            header['My-Special-Field'] = 'Very special'

            # Find the license for a given file.
            paragraph = c.find_files_paragraph('debian/rules')
            if paragraph:
                print('License for debian/rules: ', paragraph.license)

            # Dump the result, including changes, to another file.
            with io.open('debian/copyright.new', 'wt', encoding='utf-8') as f:
                c.dump(f=f)

    It is possible to build up a Copyright from scratch, by modifying the
    header and using add_files_paragraph and add_license_paragraph.  See the
    associated method docstrings.
    """

    def __init__(self, sequence=None, encoding='utf-8', strict=True):
        # type: (Optional[Union[List[str], IO[str]]], str, bool) -> None
        """ Create a new copyright file in the current format.

        :param sequence: Sequence of lines, e.g. a list of strings or a
            file-like object.  If not specified, a blank Copyright object is
            initialized.
        :param encoding: Encoding to use, in case input is raw byte strings.
            It is recommended to use unicode objects everywhere instead, e.g.
            by opening files in text mode.
        :param strict: Raise if format errors are detected in the data.

        Raises:
            :class:`NotMachineReadableError` if 'sequence' does not contain a
                machine-readable debian/copyright file.
            MachineReadableFormatError if 'sequence' is not a valid file.
        """
        super(Copyright, self).__init__()

        self.__paragraphs = []  # type: List[ParagraphTypes]

        if sequence is not None:
            paragraphs = list(deb822.Deb822.iter_paragraphs(
                sequence=sequence, encoding=encoding))
            if not paragraphs:
                raise NotMachineReadableError('no paragraphs in input')
            self.__header = Header(paragraphs[0])
            for i in range(1, len(paragraphs)):
                p = paragraphs[i]
                if 'Files' in p:
                    pf = FilesParagraph(p, strict)
                    self.__paragraphs.append(pf)
                elif 'License' in p:
                    pl = LicenseParagraph(p, strict)
                    self.__paragraphs.append(pl)
                else:
                    _complain('Non-header paragraph has neither "Files" nor '
                              '"License" fields', strict)

        else:
            self.__header = Header()

    @property
    def header(self):
        # type: () -> Header
        """The file header paragraph."""
        return self.__header

    @header.setter
    def header(self, hdr):
        if not isinstance(hdr, Header):
            raise TypeError('value must be a Header object')
        self.__header = hdr

    def all_paragraphs(self):
        # type: () -> Iterator[AllParagraphTypes]
        """Returns an iterator over all paragraphs (header, Files, License).

        The header (returned first) will be returned as a Header object; file
        paragraphs as FilesParagraph objects; license paragraphs as
        LicenseParagraph objects.

        """
        return itertools.chain([self.header], (p for p in self.__paragraphs))

    def __iter__(self):
        # type: () -> Iterator[AllParagraphTypes]
        """Iterate over all paragraphs

        see all_paragraphs() for more information

        """
        return self.all_paragraphs()

    def all_files_paragraphs(self):
        # type: () -> Iterator[FilesParagraph]
        """Returns an iterator over the contained FilesParagraph objects."""
        return (p for p in self.__paragraphs if isinstance(p, FilesParagraph))

    def find_files_paragraph(self, filename):
        # type: (str) -> Optional[FilesParagraph]
        """Returns the FilesParagraph for the given filename.

        In accordance with the spec, this method returns the last FilesParagraph
        that matches the filename.  If no paragraphs matched, returns None.
        """
        result = None
        for p in self.all_files_paragraphs():
            if p.matches(filename):
                result = p
        return result

    def add_files_paragraph(self, paragraph):
        # type: (FilesParagraph) -> None
        """Adds a FilesParagraph to this object.

        The paragraph is inserted directly after the last FilesParagraph (which
        might be before a standalone LicenseParagraph).
        """
        if not isinstance(paragraph, FilesParagraph):
            raise TypeError('paragraph must be a FilesParagraph instance')

        last_i = -1
        for i, p in enumerate(self.__paragraphs):
            if isinstance(p, FilesParagraph):
                last_i = i
        self.__paragraphs.insert(last_i + 1, paragraph)

    def all_license_paragraphs(self):
        # type: () -> Iterator[LicenseParagraph]
        """Returns an iterator over standalone LicenseParagraph objects."""
        return (p for p in self.__paragraphs if isinstance(p, LicenseParagraph))

    def add_license_paragraph(self, paragraph):
        # type: (LicenseParagraph) -> None
        """Adds a LicenceParagraph to this object.

        The paragraph is inserted after any other paragraphs.
        """
        if not isinstance(paragraph, LicenseParagraph):
            raise TypeError('paragraph must be a LicenseParagraph instance')
        self.__paragraphs.append(paragraph)

    def dump(self, f=None):
        # type: (Optional[IO[Text]]) -> Optional[str]
        """Dumps the contents of the copyright file.

        If f is None, returns a unicode object.  Otherwise, writes the contents
        to f, which must be a file-like object that is opened in text mode
        (i.e. that accepts unicode objects directly).  It is thus up to the
        caller to arrange for the file to do any appropriate encoding.
        """
        return_string = False
        if f is None:
            return_string = True
            f = io.StringIO()
        self.header.dump(f, text_mode=True)
        for p in self.__paragraphs:
            f.write('\n')
            p.dump(f, text_mode=True)
        if return_string:
            return f.getvalue()    # type: ignore
        return None

def _single_line(s):
    # type: (str) -> str
    """Returns s if it is a single line; otherwise raises MachineReadableFormatError."""
    if '\n' in s:
        raise MachineReadableFormatError('must be single line')
    return s


class _LineBased(object):
    """Namespace for conversion methods for line-based lists as tuples."""
    # TODO(jsw): Expose this somewhere else?  It may have more general utility.

    @staticmethod
    def from_str(s):
        # type: (Optional[str]) -> Iterable[str]
        """Returns the lines in 's', with whitespace stripped, as a tuple."""
        return tuple(v for v in
                     (line.strip() for line in (s or '').strip().splitlines())
                     if v)

    @staticmethod
    def to_str(seq):
        # type: (Iterable[str]) -> Optional[str]
        """Returns the sequence as a string with each element on its own line.

        If 'seq' has one element, the result will be on a single line.
        Otherwise, the first line will be blank.
        """
        l = list(seq)
        if not l:
            return None

        def process_and_validate(s):
            # type: (str) -> str
            s = s.strip()
            if not s:
                raise MachineReadableFormatError('values must not be empty')
            if '\n' in s:
                raise MachineReadableFormatError(
                    'values must not contain newlines')
            return s

        if len(l) == 1:
            return process_and_validate(l[0])

        tmp = ['']
        for s in l:
            tmp.append(' ' + process_and_validate(s))
        return '\n'.join(tmp)


class _SpaceSeparated(object):
    """Namespace for conversion methods for space-separated lists as tuples."""
    # TODO(jsw): Expose this somewhere else?  It may have more general utility.

    _has_space = re.compile(r'\s')

    @staticmethod
    def from_str(s):
        # type: (Optional[str]) -> Iterable[str]
        """Returns the values in s as a tuple (empty if only whitespace)."""
        return tuple(v for v in (s or '').split() if v)

    @classmethod
    def to_str(cls, seq):
        # type: (Iterable[str]) -> Optional[str]
        """Returns the sequence as a space-separated string (None if empty)."""
        l = list(seq)
        if not l:
            return None
        tmp = []
        for s in l:
            if cls._has_space.search(s):
                raise MachineReadableFormatError(
                    'values must not contain whitespace')
            s = s.strip()
            if not s:
                raise MachineReadableFormatError('values must not be empty')
            tmp.append(s)
        return ' '.join(tmp)


# TODO(jsw): Move multiline formatting/parsing elsewhere?

def format_multiline(s):
    # type: (Optional[str]) -> Optional[str]
    """Formats multiline text for insertion in a Deb822 field.

    Each line except for the first one is prefixed with a single space.  Lines
    that are blank or only whitespace are replaced with ' .'
    """
    if s is None:
        return None
    return format_multiline_lines(s.splitlines())


def format_multiline_lines(lines):
    # type: (List[str]) -> str
    """Same as format_multline, but taking input pre-split into lines."""
    out_lines = []
    for i, line in enumerate(lines):
        if i != 0:
            if not line.strip():
                line = '.'
            line = ' ' + line
        out_lines.append(line)
    return '\n'.join(out_lines)


def parse_multiline(s):
    # type: (Optional[str]) -> Optional[str]
    """Inverse of format_multiline.

    Technically it can't be a perfect inverse, since format_multline must
    replace all-whitespace lines with ' .'.  Specifically, this function:

      - Does nothing to the first line
      - Removes first character (which must be ' ') from each proceeding line.
      - Replaces any line that is '.' with an empty line.
    """
    if s is None:
        return None
    return '\n'.join(parse_multiline_as_lines(s))


def parse_multiline_as_lines(s):
    # type: (str) -> List[str]
    """Same as parse_multiline, but returns a list of lines.

    (This is the inverse of format_multiline_lines.)
    """
    lines = s.splitlines()
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line.startswith(' '):
            line = line[1:]
        else:
            raise MachineReadableFormatError(
                'continued line must begin with " "')
        if line == '.':
            line = ''
        lines[i] = line
    return lines


class License(collections.namedtuple('License', 'synopsis text')):
    """Represents the contents of a License field.  Immutable."""

    def __new__(cls, synopsis, text=''):
        """Creates a new License object.

        :param synopsis: The short name of the license, or an expression giving
            alternatives.  (The first line of a License field.)
        :param text: The full text of the license, if any (may be None).  The
            lines should not be mangled for "deb822"-style wrapping - i.e. they
            should not have whitespace prefixes or single '.' for empty lines.
        """
        return super(License, cls).__new__(
            cls, synopsis=_single_line(synopsis), text=(text or ''))

    @classmethod
    def from_str(cls, s):
        # type: (Optional[str]) -> Optional[License]
        if s is None:
            return None

        lines = parse_multiline_as_lines(s)
        if not lines:
            return cls('')   # type: ignore
        return cls(lines[0], text='\n'.join(itertools.islice(lines, 1, None)))

    def to_str(self):
        # type: () -> str
        return format_multiline_lines([self.synopsis] + self.text.splitlines())

    # TODO(jsw): Parse the synopsis?
    # TODO(jsw): Provide methods to look up license text for known licenses?


def globs_to_re(globs):
    # type: (Iterable[str]) -> Pattern
    r"""Returns an re object for the given globs.

    Only * and ? wildcards are supported.  Literal * and ? may be matched via
    \* and \?, respectively.  A literal backslash is matched \\.  Any other
    character after a backslash is forbidden.

    Empty globs match nothing.

    Raises MachineReadableFormatError if any of the globs is illegal.
    """
    buf = io.StringIO()
    for i, glob in enumerate(globs):
        if i != 0:
            buf.write('|')
        i = 0
        n = len(glob)
        while i < n:
            c = glob[i]
            i += 1
            if c == '*':
                buf.write('.*')
            elif c == '?':
                buf.write('.')
            elif c == '\\':
                if i < n:
                    c = glob[i]
                    i += 1
                else:
                    raise MachineReadableFormatError(
                        'single backslash not allowed at end')
                if c in r'\?*':
                    buf.write(re.escape(c))
                else:
                    raise MachineReadableFormatError(
                        r'invalid escape sequence: \%s' % c)
            else:
                buf.write(re.escape(c))

    # Patterns must be anchored at the end of the string.  (We use \Z instead
    # of $ so that this works correctly for filenames including \n.)
    buf.write(r'\Z')
    return re.compile(buf.getvalue(), re.MULTILINE | re.DOTALL)


class FilesParagraph(deb822.RestrictedWrapper):
    """Represents a Files paragraph of a debian/copyright file.

    This kind of paragraph is used to specify the copyright and license for a
    particular set of files in the package.
    """

    def __init__(self, data, _internal_validate=True, strict=True):
        # type: (deb822.Deb822, bool, bool) -> None
        super(FilesParagraph, self).__init__(data)

        if _internal_validate:
            if 'Files' not in data:
                raise MachineReadableFormatError('"Files" field required')
            if 'Copyright' not in data:
                _complain('Files paragraph missing Copyright field', strict)
            if 'License' not in data:
                _complain('Files paragraph missing License field', strict)

            if not self.files:
                _complain('Files paragraph has empty Files field', strict)

        self.__cached_files_pat = ('', re.compile(''))  # type: Tuple[str, Pattern]

    @classmethod
    def create(cls,
               files,      # type: Optional[List[str]]
               copyright,  # type: Optional[str]
               license,    # type: Optional[License]
              ):
        # type: (...) -> FilesParagraph
        """Create a new FilesParagraph from its required parts.

        :param files: The list of file globs.
        :param copyright_info: The copyright for the files (free-form text).
        :param license_info: The Licence for the files.
        """
        # pylint: disable=redefined-builtin
        p = cls(deb822.Deb822(), _internal_validate=False)
        p.files = files
        p.copyright = copyright
        p.license = license
        return p

    def files_pattern(self):
        # type: () -> Optional[Pattern]
        """Returns a regular expression equivalent to the Files globs.

        Caches the result until files is set to a different value.

        Raises ValueError if any of the globs are invalid.
        """
        files_str = self['files']
        if self.__cached_files_pat[0] != files_str:
            self.__cached_files_pat = (files_str, globs_to_re(self.files))
        return self.__cached_files_pat[1]

    def matches(self, filename):
        # type: (str) -> bool
        """Returns True iff filename is matched by a glob in Files."""
        pat = self.files_pattern()
        if pat is None:
            return False
        return pat.match(filename) is not None

    files = deb822.RestrictedField(
        'Files', from_str=_SpaceSeparated.from_str,
        to_str=_SpaceSeparated.to_str, allow_none=False)

    copyright = deb822.RestrictedField('Copyright', allow_none=False)  # type: ignore

    license = deb822.RestrictedField(
        'License', from_str=License.from_str, to_str=License.to_str,
        allow_none=False)

    comment = deb822.RestrictedField('Comment')    # type: ignore


class LicenseParagraph(deb822.RestrictedWrapper):
    """Represents a standalone license paragraph of a debian/copyright file.

    Minimally, this kind of paragraph requires a 'License' field and has no
    'Files' field.  It is used to give a short name to a license text, which
    can be referred to from the header or files paragraphs.
    """

    def __init__(self, data, _internal_validate=True):
        # type: (deb822.Deb822, bool) -> None
        super(LicenseParagraph, self).__init__(data)
        if _internal_validate:
            if 'License' not in data:
                raise MachineReadableFormatError('"License" field required')
            if 'Files' in data:
                raise MachineReadableFormatError(
                    'input appears to be a Files paragraph')

    @classmethod
    def create(cls, license):
        # type: (License) -> LicenseParagraph
        """Returns a LicenseParagraph with the given license."""
        # pylint: disable=redefined-builtin
        if not isinstance(license, License):
            raise TypeError('license must be a License instance')
        paragraph = cls(deb822.Deb822(), _internal_validate=False)
        paragraph.license = license
        return paragraph

    # TODO(jsw): Validate that the synopsis of the license is a short name or
    # short name with exceptions (not an alternatives expression).  This
    # requires help from the License class.
    license = deb822.RestrictedField(
        'License', from_str=License.from_str, to_str=License.to_str,
        allow_none=False)

    comment = deb822.RestrictedField('Comment')    # type: ignore

    # Hide 'Files'.
    __files = deb822.RestrictedField('Files')    # type: ignore


class Header(deb822.RestrictedWrapper):
    """Represents the header paragraph of a debian/copyright file.

    Property values are all immutable, such that in order to modify them you
    must explicitly set them (rather than modifying a returned reference).
    """

    def __init__(self, data=None):
        # type: (Optional[deb822.Deb822]) -> None
        """Initializer.

        :param data: A deb822.Deb822 object for underlying data.  If None, a
            new one will be created.
        """
        if data is None:
            data = deb822.Deb822()
            data['Format'] = _CURRENT_FORMAT

        if 'Format-Specification' in data:
            warnings.warn('use of deprecated "Format-Specification" field;'
                          ' rewriting as "Format"')
            data['Format'] = data['Format-Specification']
            del data['Format-Specification']

        super(Header, self).__init__(data)

        fmt = self.format   # type: ignore
        if fmt != _CURRENT_FORMAT and fmt is not None:
            # Add a terminal slash onto the end if missing
            if not fmt.endswith('/'):
                fmt += "/"

            # Upgrade http to https if that is valid
            if fmt.startswith('http:'):
                fmt = "https:%s" % fmt[5:]

            if fmt in _KNOWN_FORMATS:
                warnings.warn('Fixing Format URL')
                self.format = fmt

        if fmt is None:
            raise NotMachineReadableError(
                'input is not a machine-readable debian/copyright')
        if fmt not in _KNOWN_FORMATS:
            warnings.warn('format not known: %r' % fmt)

    def known_format(self):
        # type: () -> bool
        """Returns True iff the format is known."""
        return self.format in _KNOWN_FORMATS

    def current_format(self):
        # type: () -> bool
        """Returns True iff the format is the current format."""
        return self.format == _CURRENT_FORMAT

    # lots of type ignores due to  https://github.com/python/mypy/issues/1279
    format = deb822.RestrictedField(                    # type: ignore
        'Format', to_str=_single_line, allow_none=False)

    upstream_name = deb822.RestrictedField(              # type: ignore
        'Upstream-Name', to_str=_single_line)

    upstream_contact = deb822.RestrictedField(           # type: ignore
        'Upstream-Contact', from_str=_LineBased.from_str,
        to_str=_LineBased.to_str)

    source = deb822.RestrictedField('Source')            # type: ignore

    disclaimer = deb822.RestrictedField('Disclaimer')    # type: ignore

    comment = deb822.RestrictedField('Comment')          # type: ignore

    license = deb822.RestrictedField(                    # type: ignore
        'License', from_str=License.from_str, to_str=License.to_str)

    copyright = deb822.RestrictedField('Copyright')      # type: ignore


try:
    ParagraphTypes = Union[FilesParagraph, LicenseParagraph]
    AllParagraphTypes = Union[Header, FilesParagraph, LicenseParagraph]
except NameError:
    # ignore exception if typing is not loaded
    pass
