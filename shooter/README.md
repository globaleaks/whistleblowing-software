# shooter

a REST shooter for GLBackend, used for testing, development and perform shell controlled
client emulation. is based on **HTTPie**, a pretty curl interface for testing REST with JSON
utilities.

### Shooter.py

after the while refactor of the code, the previous curteg is became completely obsolete, and
now a new implementation is done. Its called **shooter**, is based on:

    https://github.com/jkbr/httpie

and need to be installed in your system (or in your pyenv) with:

    pip install --upgrade https://github.com/jkbr/httpie/tarball/master

### API actually supported

     '/node': 'GET' ,
     '/submission': 'GET',
     '/submission/@SID@/status': 'GET',
     '/submission/@SID@/status': 'POST',
     '/submission/@SID@/finalize': 'POST',
     '/tip/@TIP@': 'GET',
     '/tip/@TIP@' : 'POST',
     '/tip/@TIP@/comment': 'POST',
     '/tip/@TIP@/finalize': 'POST',
     '/tip/@TIP@/download': 'GET', 
     '/tip/@TIP@/pertinence': 'POST',
     '/receiver/@TIP@': 'GET',
     '/receiver/@TIP@/notification': 'GET', 
     '/receiver/@TIP@/notification': 'POST',
     '/receiver/@TIP@/notification': 'PUT',
     '/receiver/@TIP@/notification': 'DELETE',
     '/admin/node':'GET',
     '/admin/node':'POST',
     '/admin/contexts/@CID@': 'GET',
     '/admin/contexts/@CID@': 'POST',
     '/admin/contexts/@CID@': 'PUT',
     '/admin/contexts/@CID@': 'DELETE',
     '/admin/receivers/@CID@': 'GET',
     '/admin/receivers/@CID@': 'POST',
     '/admin/receivers/@CID@': 'DELETE',
     '/admin/receivers/@CID@': 'PUT',
     '/admin/modules/@CID@/notification': 'GET',
     '/admin/modules/@CID@/notification': 'POST'

default base URL is http://127.0.0.1:8082

### Usage


### JSON files


## Scripts

    submission.sh 
    
emulate a submission, in the first context presented by '/node'

    comment.sh

send a comment to a tip (need to be passed the tip globaleaks unique string, something
like: t\_DjAXRhikjKsovldfqXDswsfkPNTCopKTdenkPiRaYZCDrkUuQd as argument)
