"""
Python introspection helpers.
"""

from types import CodeType as code, FunctionType as function

def copycode(template, changes):
    names = [
        "argcount", "nlocals", "stacksize", "flags", "code", "consts",
        "names", "varnames", "filename", "name", "firstlineno", "lnotab",
        "freevars", "cellvars"
    ]
    if str is not bytes:
        names.insert(1, "kwonlyargcount")
    values = [
        changes.get(name, getattr(template, "co_" + name))
        for name in names
    ]
    return code(*values)



def copyfunction(template, funcchanges, codechanges):
    names = [
        "globals", "name", "defaults", "closure",
    ]
    values = [
        funcchanges.get(name, getattr(template, "__" + name + "__"))
        for name in names
    ]
    return function(copycode(template.__code__, codechanges), *values)


def preserveName(f):
    """
    Preserve the name of the given function on the decorated function.
    """
    def decorator(decorated):
        return copyfunction(decorated,
                            dict(name=f.__name__), dict(name=f.__name__))
    return decorator
