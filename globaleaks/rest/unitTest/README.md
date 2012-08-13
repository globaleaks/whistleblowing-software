# How perform the tests

    $ (in GLBackend/ directory)
    $ cat env-gl-set 
    #!/bin/sh
    export PYTHONPATH=`pwd`
    $ . ./env-gl-set
    $ python globaleaks/rest/api.py


In another console

    $ cd globaleaks/rest/unitTest
    $ python unitTestRest.py


REST.sh and jsoncurl.sh are testing script useful for some comparative tests, they are extremely poor.
