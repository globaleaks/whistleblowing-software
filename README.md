# GlobaLeaks

GlobaLeaks is a project aimed at creating a whistleblowing platform built on FLOSS.

This is the main repository that serves to keep track of the overall
development of the GlobaLeaks platform as a whole.

Here we collect all the knowledge that is not specific to the client or backend
component.

## GlobaLeaks 0.1

This is the first implementation of the GlobaLeaks workflow.

People interested in installing and running a GlobaLeaks node *now* should look
into running [GlobaLeaks 0.1](https://github.com/globaleaks/GlobaLeaks-0.1.git).

GlobaLeaks 0.1 is an "Adanced Prototype" and it has helped us understand the
limits of certain technological choices and lead us towards the new branch of
development.

We will keep maintaining GlobaLeaks 0.1 and make migrating to GlobaLeaks 0.2 as
seamless as possible, but it is not the main direction of development.

## GlobaLeaks 0.2

This is a full rewrite and it collects all of the experience and knowledge
gained in building GlobaLeaks 0.1.

All future development will continue in this direction.

The main components of GlobaLeaks 0.2 are
[GLClient](https://github.com/globaleaks/GLClient.git) and
[GLBackend](https://github.com/globaleaks/GLBackend.git).
[APAF](https://github.com/globaleaks/APAF.git).

[GLClient](https://github.com/globaleaks/GLClient.git) is a javascript web
application that communicates to the Backend component of GlobaLeaks. It is the
standard means for a Whistleblower, Administrator or Receiver to interact with
a GlobaLeaks node.

[APAF](https://github.com/globaleaks/APAF.git) , aka Anonymous Python Application Framework, 
is a multi-platform build system framework and a library for developing Python/Twisted based 
server applications, exposed as Tor Hidden Service, easy to be installed and managed on multiple
platforms (Windows, OSX, Debian) with a particular focus for desktop environments.


# Are you a developer?

Learn more about GlobaLeaks by checking out the [developer documentation](https://github.com/globaleaks/GlobaLeaks/wiki/Home)!

# Sneak peak of WIP

If you are dying to try out the new GlobaLeaks 0.2 you can run the following commands to start GLBackend and see the client UI.

This procedure is tested on Ubuntu 12.04

    apt-get install python-virtualenv git gcc python-dev
    git clone https://github.com/globaleaks/GLBackend
    git clone https://github.com/globaleaks/GLClient

    # It is important that they are both in the same directory
    cd GLBackend

    virtualenv -p python2.7 glenv
    source glenv/bin/activate
    pip install -r requirements.txt
    export PYTHONPATH=`pwd`
    ./bin/startglobaleaks

Now you may point your browser to http://127.0.0.1:8082/index.html and have a sneak peak at GL 0.2.

Have fun :)


