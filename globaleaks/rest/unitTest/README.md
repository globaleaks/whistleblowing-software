## How perform the tests

# unit test with curl and page retrive

    $ (in GLBackend/ directory)
    $ cat env-gl-set 
    #!/bin/sh
    export PYTHONPATH=`pwd`
    $ . ./env-gl-set
    $ python globaleaks/rest/api.py

In another console

    $ cd globaleaks/rest/unitTest
    $ python restTest_curl.py <optional:verbose> <optional:HOSTNAME:PORT>

enable the verbose dumping of the sent/receiver JSON object (or errors)

# unit test without run twisted idle loop

    $ cd globaleaks/rest/unitTest
    $ python restTest_unit.py
    TODO (@hellais can you describe this testing logic ?)

