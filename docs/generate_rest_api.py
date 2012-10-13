import inspect

from globaleaks.rest.api import spec
from utils import cleanup_docstring

def detailHandler(handler):
    ret = ""
    for method in ['get', 'post', 'put', 'delete']:
        m = getattr(handler, method)
        if m.__doc__:
            ret += "#### %s\n" % method
            docstring = cleanup_docstring(m.__doc__)
            ret += "%s\n" % docstring
    if not ret:
        ret += "_Undocumented_\n"
        ret += "see <https://github.com/globaleaks/GlobaLeaks/wiki/API-Specification>\n\n"
    return ret

paths = []
handlers = []
for resource in spec:
    path = resource[0]
    paths.append(path)
    handler = resource[1]
    handlers.append(detailHandler(handler))

print "## Summary of API"
for path in paths:
    print "* `%s`\n" % path

print "## Detailed specification"
for idx, path in enumerate(paths):
    print "### %s" % path
    print handlers[idx]


