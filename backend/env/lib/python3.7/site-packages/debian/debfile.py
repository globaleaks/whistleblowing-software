""" Representation of Debian binary package (.deb) files


Debfile Classes
===============
"""

# Copyright (C) 2007-2008   Stefano Zacchiroli  <zack@debian.org>
# Copyright (C) 2007        Filippo Giunchedi   <filippo@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function

import gzip
import tarfile
import sys
import os.path

try:
    # pylint: disable=unused-import
    from typing import (
        Any,
        Dict,
        IO,
        Iterator,
        List,
        Optional,
        Text,
        TypeVar,
        Union,
    )
except ImportError:
    # Missing types aren't important at runtime
    pass

from debian.arfile import ArFile, ArError, ArMember     # pylint: disable=unused-import
from debian.changelog import Changelog
from debian.deb822 import Deb822


DATA_PART = 'data.tar'      # w/o extension
CTRL_PART = 'control.tar'
PART_EXTS = ['gz', 'bz2', 'xz', 'lzma']  # possible extensions
INFO_PART = 'debian-binary'
MAINT_SCRIPTS = ['preinst', 'postinst', 'prerm', 'postrm', 'config']

CONTROL_FILE = 'control'
CHANGELOG_NATIVE = 'usr/share/doc/%s/changelog.gz'  # with package stem
CHANGELOG_DEBIAN = 'usr/share/doc/%s/changelog.Debian.gz'
MD5_FILE = 'md5sums'


class DebError(ArError):
    pass


class DebPart(object):
    """'Part' of a .deb binary package.

    A .deb package is considered as made of 2 parts: a 'data' part
    (corresponding to the possibly compressed 'data.tar' archive embedded
    in a .deb) and a 'control' part (the 'control.tar.gz' archive). Each of
    them is represented by an instance of this class. Each archive should
    be a compressed tar archive although an uncompressed data.tar is permitted;
    supported compression formats are: .tar.gz, .tar.bz2, .tar.xz .

    When referring to file members of the underlying .tar.gz archive, file
    names can be specified in one of 3 formats "file", "./file", "/file". In
    all cases the file is considered relative to the root of the archive. For
    the control part the preferred mechanism is the first one (as in
    deb.control.get_content('control') ); for the data part the preferred
    mechanism is the third one (as in deb.data.get_file('/etc/vim/vimrc') ).
    """

    def __init__(self, member):
        # type: (ArMember) -> None
        self.__member = member  # arfile.ArMember file member
        self.__tgz = None   # type: Optional[tarfile.TarFile]

    def tgz(self):
        # type: () -> tarfile.TarFile
        """Return a TarFile object corresponding to this part of a .deb
        package.

        Despite the name, this method gives access to various kind of
        compressed tar archives, not only gzipped ones.
        """

        if self.__tgz is None:
            name = self.__member.name
            extension = os.path.splitext(name)[1][1:]
            if extension in PART_EXTS or name == DATA_PART or name == CTRL_PART:
                # Permit compressed members and also uncompressed data.tar
                if sys.version_info < (3, 3) and extension == 'xz':
                    try:
                        import subprocess
                        import signal
                        import io

                        # pylint: disable=subprocess-popen-preexec-fn
                        proc = subprocess.Popen(
                            ['unxz', '--stdout'],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            universal_newlines=False,
                            preexec_fn=lambda:
                            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
                        )
                    except (OSError, ValueError) as e:
                        raise DebError("%s" % e)

                    data = proc.communicate(self.__member.read())[0]
                    if proc.returncode != 0:
                        raise DebError("command has failed with code '%s'" %
                                       proc.returncode)

                    buffer = io.BytesIO(data)
                else:
                    buffer = self.__member

                try:
                    self.__tgz = tarfile.open(fileobj=buffer, mode='r:*')    # type: ignore
                except (tarfile.ReadError, tarfile.CompressionError) as e:
                    raise DebError("tarfile has returned an error: '%s'" % e)
            else:
                raise DebError("part '%s' has unexpected extension" % name)
        return self.__tgz

    @staticmethod
    def __normalize_member(fname):
        # type: (str) -> str
        """ try (not so hard) to obtain a member file name in a form relative
        to the .tar.gz root and with no heading '.' """

        if fname.startswith('./'):
            fname = fname[2:]
        elif fname.startswith('/'):
            fname = fname[1:]
        return fname

    # XXX in some of the following methods, compatibility among >= 2.5 and <<
    # 2.5 python versions had to be taken into account. TarFile << 2.5 indeed
    # was buggied and returned member file names with an heading './' only for
    # the *first* file member. TarFile >= 2.5 fixed this and has the heading
    # './' for all file members.

    def has_file(self, fname):
        # type: (str) -> bool
        """Check if this part contains a given file name."""

        fname = DebPart.__normalize_member(fname)
        names = self.tgz().getnames()
        return (('./' + fname in names)
                or (fname in names))  # XXX python << 2.5 TarFile compatibility

    def get_file(self, fname, encoding=None, errors=None):
        # type: (str, Optional[str], Optional[str]) -> Union[IO[bytes], IO[str]]
        """Return a file object corresponding to a given file name.

        If encoding is given, then the file object will return Unicode data;
        otherwise, it will return binary data.
        """

        fname = DebPart.__normalize_member(fname)
        try:
            fobj = self.tgz().extractfile('./' + fname)
        except KeyError:    # XXX python << 2.5 TarFile compatibility
            fobj = self.tgz().extractfile(fname)
        if fobj is None:
            raise DebError("File not found inside package")
        if encoding is not None:
            if sys.version >= '3':
                import io
                if not hasattr(fobj, 'flush'):
                    # XXX http://bugs.python.org/issue13815
                    fobj.flush = lambda: None   # type: ignore
                return io.TextIOWrapper(fobj, encoding=encoding, errors=errors)

            # CRUFT: Python 2 only
            import codecs
            if errors is None:
                errors = 'strict'
            return codecs.EncodedFile(fobj, encoding, errors=errors)

        return fobj

    def get_content(self,
                    fname,          # type: str
                    encoding=None,  # type: Optional[str]
                    errors=None,    # type: Optional[str]
                   ):
        # type: (...) -> Optional[Union[bytes, Text]]
        """Return the string content of a given file, or None (e.g. for
        directories).

        If encoding is given, then the content will be a Unicode object;
        otherwise, it will contain binary data.
        """

        f = self.get_file(fname, encoding=encoding, errors=errors)
        content = None
        if f:   # can be None for non regular or link files
            content = f.read()
            f.close()
        return content

    # container emulation

    def __iter__(self):
        # type: () -> Iterator[str]
        return iter(self.tgz().getnames())

    def __contains__(self, fname):
        # type: (str) -> bool
        return self.has_file(fname)

    if sys.version < '3':
        def has_key(self, fname):
            # type: (str) -> bool
            return self.has_file(fname)

    def __getitem__(self, fname):
        # type: (str) ->  Optional[Union[bytes, Text]]
        return self.get_content(fname)

    def close(self):
        # type: () -> None
        self.__member.close()


class DebData(DebPart):

    pass


class DebControl(DebPart):

    def scripts(self):
        # () -> Dict[str, bytes]
        """ Return a dictionary of maintainer scripts (postinst, prerm, ...)
        mapping script names to script text. """

        scripts = {}
        for fname in MAINT_SCRIPTS:
            if self.has_file(fname):
                scripts[fname] = self.get_content(fname)

        return scripts

    def debcontrol(self):
        # () -> Deb822
        """ Return the debian/control as a Deb822 (a Debian-specific dict-like
        class) object.

        For a string representation of debian/control try
        .get_content('control') """

        return Deb822(self.get_content(CONTROL_FILE))

    def md5sums(self, encoding=None, errors=None):
        # type: (Optional[str], Optional[str]) -> Dict[Union[str, bytes], str]
        """ Return a dictionary mapping filenames (of the data part) to
        md5sums. Fails if the control part does not contain a 'md5sum' file.

        Keys of the returned dictionary are the left-hand side values of lines
        in the md5sums member of control.tar.gz, usually file names relative to
        the file system root (without heading '/' or './').

        The returned keys are Unicode objects if an encoding is specified,
        otherwise binary. The returned values are always Unicode."""

        if not self.has_file(MD5_FILE):
            raise DebError(
                "'%s' file not found, can't list MD5 sums" % MD5_FILE)

        md5_file = self.get_file(MD5_FILE, encoding=encoding, errors=errors)
        sums = {}  # type:  Dict[Any, str]

        newline = '\r\n'     # type: Union[str, bytes]
        if encoding is None:
            newline = b'\r\n'

        for line in md5_file.readlines():
            # we need to support spaces in filenames, .split() is not enough
            md5, fname = line.rstrip(newline).split(None, 1)  # type: ignore
            if sys.version >= '3' and isinstance(md5, bytes):
                sums[fname] = md5.decode()
            else:
                sums[fname] = md5  # type: ignore
        md5_file.close()
        return sums


class DebFile(ArFile):
    # pylint: disable=abstract-method
    """Representation of a .deb file (a Debian binary package)

    DebFile objects have the following (read-only) properties:
        - version       debian .deb file format version (not related with the
                        contained package version), 2.0 at the time of writing
                        for all .deb packages in the Debian archive
        - data          DebPart object corresponding to the data.tar.gz (or
                        other compressed or uncompressed tar) archive contained
                        in the .deb file
        - control       DebPart object corresponding to the control.tar.gz (or
                        other compressed tar) archive contained in the .deb
                        file
    """

    def __init__(self, filename=None, mode='r', fileobj=None):
        # type: (str, str, IO[bytes]) -> None
        ArFile.__init__(self, filename, mode, fileobj)
        actual_names = set(self.getnames())

        def compressed_part_name(basename):
            # type: (str) -> str
            candidates = ['%s.%s' % (basename, ext) for ext in PART_EXTS]
            # also permit uncompressed data.tar and control.tar
            if basename in (DATA_PART, CTRL_PART):
                candidates.append(basename)
            parts = actual_names.intersection(set(candidates))
            if not parts:
                raise DebError(
                    "missing required part in given .deb"
                    " (expected one of: %s)" % candidates)
            elif len(parts) > 1:
                raise DebError(
                    "too many parts in given .deb"
                    " (was looking for only one of: %s)" % candidates)
            else:   # singleton list
                return list(parts)[0]

        if INFO_PART not in actual_names:
            raise DebError(
                "missing required part in given .deb"
                " (expected: '%s')" % INFO_PART)

        self.__parts = {}   # type: Dict[str, DebPart]
        self.__parts[CTRL_PART] = DebControl(self.getmember(
            compressed_part_name(CTRL_PART)))
        self.__parts[DATA_PART] = DebData(self.getmember(
            compressed_part_name(DATA_PART)))
        self.__pkgname = None   # updated lazily by __updatePkgName

        f = self.getmember(INFO_PART)
        self.__version = f.read().strip()
        f.close()

    def __updatePkgName(self):
        self.__pkgname = self.debcontrol()['package']

    version = property(lambda self: self.__version)
    data = property(lambda self: self.__parts[DATA_PART])
    control = property(lambda self: self.__parts[CTRL_PART])

    # proxy methods for the appropriate parts

    def debcontrol(self):
        # type: () -> Deb822
        """ See .control.debcontrol() """
        return self.control.debcontrol()

    def scripts(self):
        # type: () -> List[bytes]
        """ See .control.scripts() """
        return self.control.scripts()

    def md5sums(self, encoding=None, errors=None):
        # type: (Optional[str], Optional[Any]) -> Dict[str, str]
        """ See .control.md5sums() """
        return self.control.md5sums(encoding=encoding, errors=errors)

    def changelog(self):
        # type: () -> Optional[Changelog]
        """ Return a Changelog object for the changelog.Debian.gz of the
        present .deb package. Return None if no changelog can be found. """

        if self.__pkgname is None:
            self.__updatePkgName()

        for fname in [CHANGELOG_DEBIAN % self.__pkgname,
                      CHANGELOG_NATIVE % self.__pkgname]:
            if self.data.has_file(fname):
                gz = gzip.GzipFile(fileobj=self.data.get_file(fname))
                raw_changelog = gz.read()
                gz.close()
                return Changelog(raw_changelog)
        return None

    def close(self):
        # type: () -> None
        self.control.close()
        self.data.close()


if __name__ == '__main__':
    deb = DebFile(filename=sys.argv[1])
    tgz = deb.control.tgz()
    print(tgz.getmember('control'))
