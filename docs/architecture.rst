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

Associated documentation
========================

Read the REST-spec.md would help in understand how client and server interact.
Read the Desgin-pattern.md would explain how the code is organized.
Read the Module-roles.md for understand the flexibility provided by GL.
And checks https://github.com/globaleaks/GLBackend/wiki

Glossary
========

`GlobaLeaks`_: is the name of our project, free software, security oriented, flexible whistleblowing platform.

`GLBackend`_: Python software exposing REST interfaces, handling the communications between WB and Receiver, characterized by NodeAdmin configurations and Modules selection.

`NodeAdmin`_: The user which run a GlobaLeaks node.

`Node`_: The name of a single GlobaLeaks installation, configured to handle submissions and notify it to the receivers.

`GlClient`_: User interface for whistleblowers and/or receivers, various implementation are possible (eg: Mobile environment, javascript or machine2machine), calls the REST interface implemented in GLBackend.

`WhistleBlower`_: is the user which perform a submission, containing the information he want communicate outside.

`Context`_: A single topic managed by a Node. A node would have more contests. Every context has differnet internal policy and goals.

`Group`_: The users which receive a Tip, more groups may stay inside the same Context.

`Receiver`_: The final user which receive a Tip, the receiver list is handled by the Group configuration, more receivers may stay inside a group.

`Submission`_: Is the action performed by the WhistleBlower. A submission trigger the creation of various Tip(s), and return a Receipt

`Receipt`_: Is the action performed by the WhistleBlower. A submission trigger the creation of various Tip(s), and return a Receipt

`Tip`_: Every users who need to interact with a submission, access thru a Tip interface: an unique personal and time expiring secret that enable a limited access in the submission.

`Modules`_: Extensions of the original software implementing new features. The modules cover specific extension environment, used to notify a receiver that a new Tip is available. Every Receiver and the NodeAdmin may modify notification settings.

`InputFlow`_: is sequence of action performed by a GL node when a new submission is provided.

`Notification`_: Method used to notify a receiver that a new Tip is available. Every Receiver and the NodeAdmin may modify notification settings.

`Delivery`_: Method used by receiver to download the submitted material, Every Receiver and the NodeAdmin may modify delivery settings.

`DiskStorage`_: Is the technological interface adopted by the Node when a file need to be saved locally.

`DataBaseStorage`_: Is the technological interface adopted by the Node, and inherit by the modules, when is required reas and write over a database table.

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

Receipt
```````

Is a secret possessed by the WhistleBlower for access at the Tip, needed 
whenever it want interact with the Tip of its submission.
When a receipt is active (until the Tip expire), its checked to be
unique.
Receipt may be configued differently for the various context.
Maybe disabled (is not returned to the WB), would be implemented
in modules (in the InputFlow hook) permitting to expand security 
functionality.
A receiver may suggest a portion of the Receipt, and the server 
need to add some random segment (a word, a number, etc).
The server sent back the receipt to the users.

Fields
``````

This is the contextual data associated with a submission. The
fields are fetched though an API that tells the client what
their names are and what is the description. The client will
optionally send the submission identifier that has been generated
in the folder upload phase.


Folder
``````

A group or a single file uploaded compose a folder.
Though this interface, a folder can be loaded and composed on the 
Node and associated with a submission. If a submission ID is not 
supplied the application will generate a submission identifier, 
that is then sent once the submission fields are sent.
The data sent to the GL Node will be encrypted client side with
an asymetric crypto system.


Receiver
````````
Receiver is the final destination for the submission process, would be
either someone formed and teched about whistleblowing environment, or
would also be not (depends from initiative working model).

Receiver receive a notification (a communication that update it about
the presence of a new Tip available to be consulted) or a delivery 
(the very submitted data: can be receiver in PUSH mode or in POP, in
example if choosse to download the avail files)

Group
`````

Group is an aggregation of Receiver for technical or personal
shared criteria.

A Receiver don't need to be specified with a specific contact data,
would be specified inside a group, permitting the administrator
to supports different media type for different receivers. In example,
someone would be notified by twitter, and then would be put in
the twitter group. someone other would receive notification via
email, and then is kept in email group. Every group has a different
module handling the contact type.

Group would be also relative a specific kind of receivers, and the
NodeAdmin may choose if permit to the whistleblower the ability 
to select which group interact to.


DiskStorage
-----------

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

DataBaseStorage
---------------

GlobaLeaks should supports various different interfaces
for database. Those interface would be loaded by the 
administrator choose, and are used by all the GL componentes.

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

As the modular ability of GlobaLeaks permit, the most of the secury 
feature would be enabled selecting an appropriate module.
By theory, a Node Administrator need a threat model for their 
initiative, and need to select the security features properly.

Security feature can range between an enforcing policy of configuration,
example: permit only submission thru Tor network instead of Tor2Web 
users, or, permit only submision with a receipt long almost 16 bytes.

Or Security feature can cover issue related in receiver communication,
like, enabling a module that disable all the receiver who have not
yet upload a public GPG key, for receive secure notifications.

Receipt security
````````````````

Receipt has the property to be unique for every node. A node with tons of
submission, anyway need unique receipt for every WB Tip.
This cause that the receipt can't be choosed by the users, but need to 
be (partially or totally) generated by the node, in order to avoid collisions

A Node can be configured for: do not release Receipt (WB has not further
access to their submission), generate an entire new Receipt (like the emulation
of one or more phone number, for be save in the address book) or generate a
partially choosen receipt, in example, if the WB choose "RobotUnicorn" the
server would accept it, add a random number or string, and communicate back to
the WB: "RobotUnicorn-45625".

Notification and Delivery
-------------------------

The notification and delivery system is built to be modular. Notification and
delivery systems are configured and setup by the node administrator. Once the
delivery of the submission is completed the notification of it is fired and put
into the notification queue. The notification queue can either be flushes
immediately (if the receiver is configured to receive real-time notifications)
or after a certain threshold is reached (if the receiver has been configured to
receive notification digests).

Every notification and delivery can create their own REST interface, and 
every module can define a series of field that need to be configured by 
administrator or receivers.

InputFlow
---------

InputFlow is the name given to the module that manage the various check 
performed when a submission is receiver, or under the process of 
being accepted. Like every module, permit administrator settings and 
can expose addictional REST interfaces.


GLClient
========

The UI should be a separated component that is able to hook up the GL
backend. The main UI will be developed in JavaScript and it will allow
for WB to securely submit data. 

The client adapt in automatic way to the node supports and mandatory 
fields.

The localized texts apre provided by the server and the language are
selected only client side.

Application Packaging
=====================

Application Packaging would be provided by the Tor project, sponsored 
by Google Summer Of Code, called APAF (Anonymous Python Application
Framework): https://github.com/mmaker/APAF
