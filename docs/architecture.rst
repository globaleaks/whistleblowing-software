=======================
GlobaLeaks Architecture
=======================

0. `Glossary`_
1. `Overview`_
2. `GLBackend`_

    1. `Submission`_
    2. `Storage`_
    3. `Status Page`_
    4. `Notification and Delivery`_

3. `GLClient`_
4. `Application Packaging`_

Glossary
========

`Submission`_: is the action performed by an user.

`Tip`_: The name of a single submission inside the GlobaLeaks system.

`WhistleBlower`_: is the user which perform a submission, containing the information he want communicate outside.

`Receiver`_: The user which receive a Tip.

`GlobaLeaks`_: is the name of our project, free software, security oriented, flexible whistleblowing platform.

`Node`_: The name of a single GlobaLeaks installation, configured to handle submissions and notify it to the receivers.

`NodeAdmin`_: The user which run a GlobaLeaks node.

`GLBackend`_: Python software exposing REST interfaces, based on twisted and sqlalchemy, manage the submission logic.

`GlClient`_: User interface for whistleblowers and/or receivers, various implementation are possible (eg: Mobile environment, javascript or machine2machine), calls the REST interface implemented in GLBackend.

`Notification`_: Method used to notify a receiver that a new Tip is available. Every Receiver and the NodeAdmin may modify notification settings.

`Delivery`_: Method used by receiver to download the submitted material, Every Receiver and the NodeAdmin may modify delivery settings.


Overview
========

Globaleaks is a project aimed at creating a technology that
enables anyone, even not technically skilled, to setup a
whistleblowing platform. GlobaLeaks, from now on GL, is built
from the groud up with security and privacy by default.

GlobaLeaks should be flexible to most needs and the various
components of GL should be able to exist even on their own
and be developed indipendently.
The main components are the `GLBackend`_, that handles
the interaction with all the other sub-components. The `GLClient`_
that is the means through which the user is able to
interact with GL software. The `Notification and Delivery`_ system,
that signals the `Receivers`_ of the existance of material on the GL
Node. The `Storage`_ system, that is responsible for
storing the data and/or metadata associated with the WB submission.

GLBackend
=========

The backend system will expose a REST interface that allows any
application to interact with it.
The functionalities of `Submission`_, `Storage`_, `Status Page`_
and `Notification and Delivery`_ should be highly modularized.
GlobaLeaks should be able to function properly even by removing
the `Status Page`_ and `Notification and Delivery`_ components.

Submission
----------

This interface enables a client to load a submission onto the
GL node. Through this component the client application learns
what fields are supported by the globaleaks nodes and its
properties.

The submission system has anti-spam features allowing to configure a captcha
that is activated once a certain submission/time threshold is reached.

Fields
``````

This is the contextual data associated with a submission. The
fields are fetched though an API that tells the client what
their names are and what is the description. The client will
optionally send the submission identifier that has been generated
in the material upload phase.


Material
````````

Though this interface material can be loaded on the Node and
associated with a submission. If a submission id is not supplied
the application will generate a submission identifier, that
is then sent once the submission fields are sent.
The data sent to the GL Node will be encrypted client side with
an asymetric crypto system.

Storage
-------

GlobaLeaks should support various different storage mechanisms
The storage interface should be designed in a way that it
is agnostic to the underlying system that will be used to
save the information.
If specified the node administrator should be able to configure
that the infomration stored on the node is encrypted with
his symetric key or the public keys of all the receivers.

Possible storage systems that should be implemented are:
Locally to drive, SCP, online file storage services,
tahoe-lafs.

Status Page
-----------

This is the page that keeps track of a client submission. Is enables
both `Receivers`_ and WB to access a submission that is present on
a GL Node. This interface will return the list of fields with
their value. This page will also be called Tip.

Comments
````````

Each Tip also has a comment board that allows secure communication
between the `Receivers`_ and the WB. The `Receiver`_ can use this to get
extra information on the submission and prompt the WB to upload new
material.

Statistics
``````````

Every time a `Receiver`_ visits a Tip page and downloads some material
the view and download counters are incremented. It is possible to
interrogate to get a list of views for every `Receiver`_ from any
authenticated `Receiver`_ Tip page.

Deletion
````````

A `Receiver`_ is able to delete any Tip associated with his profile.
When all the `Receivers`_ have deleted there Tips or all of them have
expired the material is removed and the database in cleaned of the
submission entry.

Security
````````

TODO.

Notification and Delivery
-------------------------

The notification and delivery system is built to be modular. Notification and
delivery systems are configured and setup by the node administrator. Once the
delivery of the submission is completed the notification of it is fired and put
into the notification queue. The notification queue can either be flushes
immediately (if the receiver is configured to receive real-time notifications)
or after a certain threshold is reached (if the receiver has been configured to
receive notification digests).


GLClient
========

The UI should be a separated component that is able to hook up the GL
backend. The main UI will be developed in JavaScript and it will allow
for WB to securely submit data.

Application Packaging
=====================

Note: this is just a copy in date 30-01-2012 of the document present
on the etterpad https://piratenpad.de/p/AnonymousWebApplicationFramework.
Look at the etterpad for the updated version of this doc.

Goal
----

The anonymous web application framework goal is to provide a web
application environment that automatically publish itself to the
Tor network as a Tor Hidden Service.

The framework allow to build Python Tornado-based Web Application
deliverying the apps as a Desktop Application (Program.exe /
Program.app) or as a Nix package, so that it would extremely reduce
the complexity to "run a server anonymously", even on a PC at home.

That way it would be possible to easily build app web application
that run on self-contained webserver that got automatically published
anonymously as Tor Hidden Services, without the need to have a public
ip address, buy a server or a domain.

The framework contain built-in and self-contained all the technologies
required:
* Python
* Tor
* TornadoWeb

Example use cases
-----------------

An ONG would like to easily setup a Whistleblowing site on it's own
pc at office by using the framework integrated version of GlobaLeaks
http://globaleaks.org .
A private person in a sensitve environment may deploy a temporary web
chat application running on it's Windows PC, exposed via Tor Hidden
Service, to handle sensitive untraceable encrypted chat.
A group of person would like to setup an email-server on Tor Hidden
Service running the server at-home of one of the group on it's
macintosh by using the framework integrated version of
http://lamsonproject.org by developing also a simple tornadoweb based
management application.

Startup Procedure
-----------------

- First Startup Procedure
`````````````````````````

The first time the application starts it must uncompress itself and
create the directory structure it need to operate.
It may be required to execute specific scripts and/or other software
to adjust system config, so the startup procedure must allow to easily
add custom scripts.
The application automatically setup the appropriate configuration
files for the applications built-in (Tor, TornadoWeb, TornadoWeb
Applications).

- Splash Screen
```````````````

The application at startup display a splash screent hat contain a
progressbar with the startup information.
The image of the splash screen must be of ease modification (it
may be a PE32 resources on windows, or a file on MacOSX/Linux) or change.

- Database initialization
`````````````````````````

The first time the application start, it must initiatlize the database
with the application schema and initialization data provided with the
build-system.

Default Web Application
The default web application built within the Anonymous Web Application
framework include several functionalities available trough a
minimalistic web interface:

- Tor Hidden Service Setup
``````````````````````````

GlobaLeaks relies on Tor Hidden Services for exposing itself to the internet.
Tor can be configured to automatically create a Tor Hidden Service at startup.
The web application automatically detect if Tor has properly setup a Tor Hidden
Service and read it's .onion domain name.

- Tor Startup
`````````````

The application let the user to see the status of Tor, to stop/start/restart it

- Tor Configuration
```````````````````

The application let the user edit the default Tor configuration file, save it.

- Tor Hidden Service reachability test
``````````````````````````````````````

The application let the user check if the Tor Hidden Service is properly reachable by
making a an outgoing connection and seeing as a Tor client that the Tor Hidden Service
is working properly (make sure that the Tor HS is published
to the DA, by default this is done every 10 minutes, but can be tweaked to be less).

- Tor2web publishing
````````````````````

Tor Hidden Services are automatically exposed trough the internet by the Tor2web project
(http://www.tor2web.org).
The node by default is automatically exposed to via Tor2web, must it must be possible to
disable inbound connection coming from Tor2web.
The web application let the user to disable/re-enable inbound connections via Tor2web.
Tech: This can be done by looking at the X-Tor2web: HTTP header

- Configure Bind Address
````````````````````````

The application let the user define the bind address of the application.
By default the application only bind to 127.0.0.1 but it may be possible to bind it also
on other IP address or 0.0.0.0 .

- User interface
````````````````

The status of the node and the setup procedure should be configurable from a user interface.
We should figure out the best way to present this, but at least insert into the application
logic the fact that the user will be guided through
a wizard to setup their node. They will also be shown the current status of the node.

- Browser Startup
`````````````````

The application when started and initiatlized must automatically open the system browser
on http://localhost:8080 (or other port where the tornadoweb listen)

Security Features
-----------------

Outbound Connection Torrification
`````````````````````````````````

The framework must automatically provide support to make anonymous outbound connection via Tor.
The entire web application framework (Tornadoweb) should be forbidden to make any outbound
connections directly and have all connections automatically torrified.
A possible approach would be to directly override DNS Resolution and TCP outbound socks of
Python interpreter using torsocks on Linux/OSX and torcap/freecap on Win32.
Torcap: http://www.freehaven.net/~aphex/torcap/
Freecap: http://www.freecap.ru/eng/
TorSocks: http://code.google.com/p/torsocks/
note: It probably may require some specific win32 coding in order to make the Python32.exe
to have torrified dns-query/tcp-sockets automatically.

Reduced Privileges for Tornadoweb
`````````````````````````````````

The application should start TornadoWeb (it will be tornado based web app) with reduced
priviledges using the native provided functionalities to restrict the application.
Win32: TODO: what can we use???
OSX: Sandbox
Linux: AppArmor profile?


Build system
------------

The build system must be configurable and should allow easy configuration of the main behavior and:
- third party application dependancy (es: Tor, p7zip, gpg)
- python libraries application dependancy (es: socksify)

The build system must be as cross-platform as possible and must be able to deliver self-contained
installable packages for:
- Win32: MyApplication.exe
- OSX: MyApplication.app (inside an Application.dmg container)
- Linux: Deb build

- Win32 Builder

Related links of possible base framework to use:
- http://www.py2exe.org/
- http://www.pyinstaller.org/

- Mac OS X Builder

On OSX it should be a self contained MyApplication.app with inside the python interpreter. Possible
 projects to look at are:
py2app - http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html

- Tor downloader
The buildsystem should download latests release of Tor for the appropriate platform and extract the
required files into the build structure, in order to be packaged within the application.

Documentation
-------------

The Anonymous Web Application Framework must provide detailed documentation on:
- how to setup the build environment (eventually on multiple operating system)
- how to customize your own enviroment for your own anonymous web application
- any specific documentation on particular procedures and/or internal structure



