=======================
GlobaLeaks Architecture
=======================

1. `Overview`_
2. `GLBackend`_

    1. `Submission`_
    2. `Storage`_
    3. `Status Page`_
    4. `Notification and Delivery`_

3. `GLClient`_
4. `Application Packaging`_

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
interact with GL software. The `Notification system`_,
that signals the targets of the existance of material on the GL
Node. The Storage system (see 1.4), that is responsible for
storing the data and/or metadata associated with the WB submission.

GLBackend
=========

The backend system will expose a REST interface that allows any
application to interact with it.

Submission
----------

This interface enables a client to load a submission onto the
GL node.

Material
````````

Though this interface material can be loaded on the Node and
associated with a submission. If a submission id is not supplied
the application will generate a submission identifier, that
is then sent once the submission fields are sent.
The data sent to the GL Node will be encrypted client side with
an asymetric crypto system.

Fields
``````

This is the contextual data associated with a submission. The
fields are fetched though an API that tells the client what
their names are and what is the description. The client will
optionally send the submission identifier that has been generated
in the material upload phase.

Storage
-------

TODO.

Status Page
-----------

a TULIP is a Temporary Unique Information Provider. Is enables
both Targets and WB to access a submission that is present on
a GL Node. This interface will return the list of fields with
their value.

Comments
````````

Each TULIP also has a comment board that allows secure communication
between the targets and the WB. The target can use this to get
extra information on the submission and prompt the WB to upload new
material.

Statistics
``````````

Every time a target visits a TULIP page and downloads some material
the view and download counters are incremented. It is possible to
interrogate to get a list of views for every target from any
authenticated target TULIP page.

Deletion
````````

A target is able to delete any TULIP associated with his profile.
When all the targets have deleted there TULIPs or all of them have
expired the material is removed and the database in cleaned of the
submission entry.

Security
````````

TODO.

Notification and Delivery
-------------------------

TODO.


GLClient
========

The UI should be a separated component that is able to hook up the GL
backend. The main UI will be developed in JavaScript and it will allow
for WB to securely submit data.



