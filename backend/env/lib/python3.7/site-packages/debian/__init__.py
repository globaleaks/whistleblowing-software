""" Tools for working with Debian-related file formats """

__version__ = ""

try:
    # pylint: disable=no-member
    import debian._version     # type: ignore
    __version__ = debian._version.__version__     # type: ignore

except ImportError:
    try:
        # Try to extract the version from the package changelog and
        # determine whether it is a post-release or pre-release version.
        import os.path
        import debian.changelog
        changelog_filename = os.path.join(
            os.path.dirname(__file__), '..', '..', 'debian', 'changelog')
        with open(changelog_filename, 'rb') as fh:
            c = debian.changelog.Changelog(fh)
            version = str(c.get_version())
            mark = "~" if c.distributions == 'UNRELEASED' else "+"
    except:    # pylint: disable=bare-except
        # Fake a version string in desperation
        version = '0.0.0'
        mark = '-'

    import datetime
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d")
    __version__ = "%s%sgit%s" % (version, mark, timestamp)
