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

GLBackend is written in Python version [2.7](http://docs.python.org/whatsnew/) 
and is mostly based on [twisted](twistedmatrix.com). For more informations see [requirements.txt](https://github.com/globaleaks/GLBackend/blob/master/requirements.txt)

# Getting Started

See wiki page [Setting up Development Environment](https://github.com/globaleaks/GLBackend/wiki/Setting-up-development-environment)

Emulate the starting wizard using:

   cd shooter/
   ./wizard.sh

  * shooter.py act like a client and is update with the interface supported in GLBacked. 
  * The script creating the first context and receivers, emulating the wizards that would be
    implemented in GLClient.

# Documentation

  * [Main GlobaLeaks documentation](https://github.com/globaleaks/GlobaLeaks/wiki/Home)
  * [GLBackend specific documentation](https://github.com/globaleaks/GLBackend/wiki/Home)
  * [APAF](https://github.com/globaleaks/APAF/wiki/Home): is the package manager developed for
    expose GLBackend as [Tor](http://www.torproject.org) [hidden service](https://www.torproject.org/docs/tor-hidden-service.html.en).

# Testing the software
```
 $ cd GLBackend/ 
 $ trial globaleaks
```

[GLBackend/shooter](https://github.com/globaleaks/GLBackend/tree/master/shooter), can be used by hand or using the shell scripts. Those perform a sequence of operation emulating the behavior of one or more users.
