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


### Usage

default base URL is http://127.0.0.1:8082

python shooter.py <API> <method> <parms> [verbose]

API would be an human readable string, like 'submission', or an unique code (URTA)
the method need to be specify, otherwise is assumed GET

the parameters are the globaleaks unique string that act as identifier of the resource,
in example:

t\_DjAXRhikjKsovldfqXDswsfkPNTCopKTdenkPiRaYZCDrkUuQd is a Tip identified (start with t\_)
c\_oewretrytuyhgfddsogf is a Context identifier (start with c\_)
r\_cnioniewnvfiewnfowif is a Receiver identifier (start with r\_)

Those user supply parameter are exchanged with the special keyword (@KEYWORD@) present in the
URL or in the JSON files.

they need to be specified with an appropriate keyword:

cid (and follow a context unique string)
tip (and follow a Tip unique string)
rid (and follow a Receiver unique string)
sid (and follow a Submission unique string)

some example:

shooter.py A2 GET cid c\_QzytUIQsoFlbReibfwLY verbose 
shooter.py A3 PUT raw \"c\_nyfyUKGeVcNdLfZwfckK\",\"c\_QzytUIQsoFlbReibfwLY\" rid r\_nyfyUKGeVcNdLfZwfckK
shooter.py U3 GET sid s\_VeLvSDfpKsxUdGLHEDDKWFBIAnTrMbbuqSPuEYylJpkxSozTmd

### printing options

if 'verbose' option is included in the command line, the command output contain the JSON
request and the JSON response. Its render with HTTPie and is fancy :)
but for the automatized scripts, is used the option "print-". Followed by a JSON field,
the output is only the content of the selected field, in example:

$ python shooter.py U1 GET print-name
uncofigured name
$ python shooter.py A1 GET print-context\_gus
c\_zBCyBUsQNAIsyqEJEsrT
$ python shooter.py A2 GET cid c\_zBCyBUsQNAIsyqEJEsrT print-receiver\_gus
r\_WUYXasvtYfXygtcODcSY
$ python shooter.py A3 GET rid r\_WUYXasvtYfXygtcODcSY print-notification\_fields
vecna@globaleaks.org

### JSON files


## Scripts

    wizard.sh

emulate the wizard at the startup (create the first context and the firsts receivers)

    submission.sh 
    
emulate a submission, in the first context presented by '/node'

    comment.sh

send a comment to a tip (need to be passed the tip globaleaks unique string, something
like: t\_DjAXRhikjKsovldfqXDswsfkPNTCopKTdenkPiRaYZCDrkUuQd as argument)

    admincycle.sh

emulate the lifecycle of an administrator, performing CURD in context and recevers
