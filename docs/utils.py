def cleanup_docstring(docstring):
    doc = ""
    stripped = [line.strip() for line in docstring.split("\n")]
    doc += '\n'.join(stripped)
    return doc

