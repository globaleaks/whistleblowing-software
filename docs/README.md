'generate\_docs.py' generate the reStructuredText upage here published:
(TODO)[https://github.com/globaleaks/GlobaLeaks/wiki/TODO]

## Why and How use it

Everytime in the handlers/\*.py files or in messages/\*.py files, something is modified (code
and docustring **need** to be always updated in the same time), executing 

    python generate_docs.py

Would generate those files:

    API.reST (present in .gitignore)
    API.wsld (TODO)
    API.json (TODO)

### Why reStructuredText

  * Because is supported between GitHub wiki formats
  * Because don't need to be modified by hand
  * Because supports Table of Content and anchor links




