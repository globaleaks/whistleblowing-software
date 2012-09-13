# GLBackend

This is the server side component of GlobaLeaks. It is through this piece of
software that the Node Administrator is able to anonymously setup and expose
GlobaLeaks Node.

It is implemented based on Twisted (using cyclone) and uses Storm as a
database.

**Warning** This version of software is under heavy development and is not
reccommended to be used by anybody.

If you are interested in running a GlobaLeaks node, you should try
[GlobaLeaks 0.1](https://github.com/globaleaks/globaleaks-0.1) the currently
"stable" release.

# Dependencies

* Python 2.7
* Cyclone
* Storm
* Transaction
* Zope component


# Getting Started

We highly recommend you use virtualenv to handle the dependencies of
globaleaks.

Once you have virtual env this is what you need to get GLBackend up and
running:

    virtualenv2 ENV
    source ENV/bin/activate
    pip install transaction zope.component twisted cyclone storm

How install them in a debian based environment:

    apt-get install python python2.7-dev python-transaction python-pip python2.7-zope.component
    pip install cyclone storm

# Documentation

  * [Main GlobaLeaks documentation](https://github.com/globaleaks/GlobaLeaks/wiki/Home)
  * [GLBackend specific documentation](https://github.com/globaleaks/GLBackend/wiki/Home)
  * [APAF](https://github.com/globaleaks/APAF/wiki/Home): is the package manager developed for
    expose GLBackend as [Tor](http://www.torproject.org) [hidden service](https://www.torproject.org/docs/tor-hidden-service.html.en).

# Testing the software

WEB API (a.k.a. REST unitTest) is partially developed, check it out in [Rest testing](globaleaks/rest/unitTest/README.md)

