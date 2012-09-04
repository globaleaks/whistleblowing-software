GlobaLeaks
==========

GlobaLeaks empowers people to report on malpractice and abuse on a local level anonymously. By blowing the whistle on entities people are able to transform information into action.
The flexibility of GlobaLeaks make it suitable for various different kinds of whistleblowing initiatives. An activist should be enabled to use the GlobaLeaks platform but it should scale
to also be applied to a corporation, public administration or newspaper.

Dependencies
============

* Python 2.7
* Cyclone
* Storm
* Transaction
* Zope component


Getting Started
===============

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

Documentation
=============

For an overview of the GlobaLeaks architecture check out the
`Architecture https://github.com/globaleaks/GLBackend/blob/master/docs/to-move-to-main-repo/architecture.rst`_ doc.
TODO: This is a temporary location, getting moved to main GL repo

Testing the software
====================

Actually only REST unitTest is partially developed, check it out in `Rest testing <globaleaks/rest/unitTest/README.md>`_.


Previous release
================

`GlobaLeaks 0.1 <https://github.com/globaleaks/globaleaks-0.1>`_ Is the usable release.
