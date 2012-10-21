## shooter

a REST shooter for GLBackend, used for testing, development and perform shell controlled
client emulation.

### Recently changed

after the while refactor of the code, the previous curteg is became completely obsolete, and
now a new implementation is done. Is based on:

    https://github.com/jkbr/httpie

and need to be installed in your system (or in your pyenv) with:

    pip install --upgrade https://github.com/jkbr/httpie/tarball/master

### Actual API

     '/node': 'GET' ,
     '/submission': 'GET',
     '/submission/__SID__/status': 'GET',
     '/submission/__SID__/status': 'POST',
     '/submission/__SID__/finalize': 'POST',
     '/tip/__TIP__': 'GET',
     '/tip/__TIP__' : 'POST',
     '/tip/__TIP__/comment': 'POST',
     '/tip/__TIP__/finalize': 'POST',
     '/tip/__TIP__/download': 'GET', 
     '/tip/__TIP__/pertinence': 'POST',
     '/receiver/__TIP__': 'GET',
     '/receiver/__TIP__/notification': 'GET', 
     '/receiver/__TIP__/notification': 'POST',
     '/receiver/__TIP__/notification': 'PUT',
     '/receiver/__TIP__/notification': 'DELETE',
     '/admin/node':'GET',
     '/admin/node':'POST',
     '/admin/contexts/__CID__': 'GET',
     '/admin/contexts/__CID__': 'POST',
     '/admin/contexts/__CID__': 'PUT',
     '/admin/contexts/__CID__': 'DELETE',
     '/admin/receivers/__CID__': 'GET',
     '/admin/receivers/__CID__': 'POST',
     '/admin/receivers/__CID__': 'DELETE',
     '/admin/receivers/__CID__': 'PUT',
     '/admin/modules/__CID__/notification': 'GET',
     '/admin/modules/__CID__/notification': 'POST'

default base URL is http://127.0.0.1:8082

### Usage


