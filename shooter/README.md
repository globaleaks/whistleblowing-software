# shooter

a REST shooter for GLBackend, used for testing, development and perform shell controlled
client emulation. is based on **HTTPie**, a pretty curl interface for testing REST with JSON
utilities.

### Requirement

after the while refactor of the code, the previous curteg is became completely obsolete, and
now a new implementation is done. Its called **shooter**, is based on:

    https://github.com/jkbr/httpie

and need to be installed in your system (or in your pyenv) with:

    pip install --upgrade https://github.com/jkbr/httpie/tarball/master

## Easy testing

    rm -rf _gldata
    bin/startglobaleaks

    cd shooter
    ./admincycle

Admin cycle perform twenty operations performable by a Node Administrator, and store
intermediary status with assertion in /tmp directory. 

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
    task (statistics|welcome|tip|delivery|notification|cleaning|digest)
    dump (itip|wtip|rtip|receivers|comment|profiles|rcfg|all|count|context)
    pid (Profile unique string)
    cn (configuration number)

in the JSON files is possibile specifiy also raw JSON data. If you make an assignment works
like an Unicode string, but for integer, boolean, list or dictionary, you need raw assignment.
For this reason, exists also the keyword:

    raw (followed by something like: \"blah\",\"ooo\" with escaped quotes)

some example:

shooter.py A2 GET cid c\_QzytUIQsoFlbReibfwLY verbose 
shooter.py A3 PUT raw \"c\_nyfyUKGeVcNdLfZwfckK\",\"c\_QzytUIQsoFlbReibfwLY\" rid r\_nyfyUKGeVcNdLfZwfckK
shooter.py U3 GET sid s\_VeLvSDfpKsxUdGLHEDDKWFBIAnTrMbbuqSPuEYylJpkxSozTmd

## API list and shortname

Under refactor with generate\_doct review.

### printing options

if 'verbose' option is included in the command line, the command output contain the JSON
request and the JSON response. Its render with HTTPie and is fancy :)
but for the automatized scripts, is used the option "print-". Followed by a JSON field,
the output is only the content of the selected field.

Follow an example that query in U1 (/node) for the name of the GL node, query in A1
(/admin/node) for get the identifier of a context (called context\_gus), get in the admin
interface informations about the selected context, using A2 (/admin/contexts) 

    $ python shooter.py U1 GET print-name
    uncofigured name
    $ python shooter.py A2 GET print-context\_gus
    c\_zBCyBUsQNAIsyqEJEsrT

using 

    $ python shooter.py help

print the short-name (A1, R1, etc) table and relationship with the path.

### JSON files

TODO, or TO BE removed for an easier configuration file.

## Scripts

    wizard.sh

emulate the wizard at the startup (create the first context and the firsts receivers)

    submission.sh 
    
emulate a submission, in the first context presented by '/node'

    comment.sh

send a comment to a tip (need to be passed the tip globaleaks unique string, something
like: t\_DjAXRhikjKsovldfqXDswsfkPNTCopKTdenkPiRaYZCDrkUuQd as argument)

    admincycle.sh

emulate the lifecycle of an administrator, performing CURD in context and recevers,
assignment and sumbmission.

    escalate.sh

Test pertinence vote, in order to make a Tip escalate
