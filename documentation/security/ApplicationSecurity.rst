====================
Application security
====================
The GlobaLeaks software conforms to industry standard best practices for application security by following OWASP Security Guidelines.

GlobaLeaks is made up of two main software components: a Backend and a Client.
The Backend is a python backend that runs on a physical backend and exposes a REST API which the Client interacts with.
The Client is a client side web application that interacts with Backend only through XHR.

Key concepts
============
This section explains the key security concepts when a Whistleblower submits a Report to a number of Recipients through GlobaLeaks.

Report
------
A report is a submission created by a Whistleblower stored in the Backend’s database.

A report is composed by the following elements:

* Questionnaire’s answers – structured and unstructured answers to the submission questionnaire;
* Files – constrained to a max size by the Administrator;
* Comments – text written by either the Whistleblower or by the recipients, which is visible to all the Recipients and to the Whistleblower;
* Messages – one to one messages between the Whistleblower and a Recipient;
* Metadata – including for example the time of Report creation, date of last access by users, number of views, number of files etc.

After a configurable amount of time a Report expires and is deleted and securely overwritten by the Backend. After deletion neither the Recipients or the Whistleblower are able to access the Report..

As well after a configurable amount of time since the last access to the Report, the Whistleblower loses the possibility to access its own report.

Whistleblower interactions with the platform
--------------------------------------------
A Whistleblower can access the platform, read and fill the submission questionnaire filing a report and eventually attaching evidence of the fact reported.

Every time a Whistleblower performs a new Submission on a GlobaLeaks platform a Report is created and the Whistleblower is given a randomly generated receipt. This Receipt is an authentication secret composed by 16 digits (e.g: 5454 0115 3135 3982) that acting as an anonymous authentication password lets Whistleblowers access their own Reports.

Recipient interactions with the platform
----------------------------------------
Any time a Report is submitted by a Whistleblower, Recipients are notified via email and they could then access the report by clicking on a link and inserting their own personal password.
Alternatively the user can access the platform via the Login interface and then access the lists of existing Reports.

When Recipients view a Report, they see the could read answers to the submission questionnaire, access the evidences attached and read some of the metadata collected by the platform like for example information about the time of the submission and the possible further communication.

If Recipients has configured a PGP encryption key then every notification sent by the platform to Recipients will be encrypted with their public key.

Authentication
==============
This section describes the authentication possibilities implemented by the system.

Due to the fact that the Backend may be deployed to be accessible via a Tor Onion Service and via HTTPS, the authentication endpoints for each user role may vary depending on the configuration.

Authentication matrix
---------------------
The table below summarizes the authentication methods for each user role.

.. csv-table::
   :header: "User type", "Authentication method"

   "Administrator", "Username and password"
   "Recipient", "Username and password"
   "Whistleblower", "Receipt"
   "M2M", "API token"


Authentication methods
----------------------
Supported authentication methods are described as follows.
Password
Administrators and Recipients use password based authentication.

By accessing the GlobaLeaks login interface, Administrators and Recipients need to insert their respective username and password. If the password submitted is valid, the system grants access to the functionality available to that user.
Receipt
Whistleblowers access their Reports by using a Receipt, which is a randomly generated 16 digits sequence created by the Backend when the Report is first submitted.

The reason of this format of 16 digits is that it resembles a standard phone number, making it easier for the whistleblower to conceal the receipt of their submission and give them plausible deniability on what is the significance of such digits.

As for a password based authentication, the Backend does not store a cleartext version of the Receipt but just an hash subject to a salt.
API token
A system integrated with GlobaLeaks could perform authenticated admin operations with an API token that is implemented as a random secret of 32 symbols in the space 0-9a-zA-Z.

This feature is optional and disabled by default.

Password security
=================
The following password security measures implemented by the system.

Authentication security
-----------------------
The confidentiality of the transmission of authentication secrets is protected by either Tor Onion Services v3 or TLS version 1.2+

Password storage
----------------
Password are never stored in plaintext but the system maintain at rest only an hash. This apply to every authentication secret included whistleblower receipts.

The platform stores Users’ passwords hashed with a random 128 bit salt, unique for each user.

Passwords are hashed using Argon2: https://en.wikipedia.org/wiki/Argon2

The hash involves a per-user salt for each user and a per-system salt for each whistleblower.

Password strength
-----------------
The system enforces the usage of complex password by implementing a custom algorithm necessary for ensuring a reasonable entropy of each authentication secret.

Password are scored in three levels: strong, acceptable, unusable.
A strong password should be formed by capital letters, lowercase letters, numbers and a symbols, be at least 12 characters long and include a variety of at least 10 different inputs.
An acceptable password should be formed by at least 3 different inputs over capital letters, lowercase letters, numbers and a symbols, be at least 10 characters and include a variety of at least 7 different inputs.

Two factor authentication (2FA)
-------------------------------
Users are enabled to enroll for Two Factor Authentication via their own preferences.
The system implements Two Factor Authentication (2FA) based on TOTP as for `RFC 6238 <https://tools.ietf.org/rfc/rfc6238.txt>`_

Password change on first login
------------------------------
The system enforces users to change their own password at their first login.
Administrators could as well enforce password change for users at their next login.

Periodic password change
------------------------
The system enforces users to change their own password every 3 months.
This period is configurable by administrators.

Proof of work on login
----------------------
The  system implements a proof of work on every login.
Each client should request a token, solve the proof of work and wait a timeout for the token to become valid.
This feature is intended to slow down possible attacks requiring more resources to users in terms of time, computation and memory.

Slowdown on failed login attempts
---------------------------------
The system identifies multiple failed login attempts and implement a slowdown procedure where an authenticating client should wait up to 42 seconds to complete an authentication.
This feature is intended to slow down possible attacks requiring more resources to users in terms of time, computation and memory.

Password recovery
-----------------
In case of password loss users could request a password reset via the web login interface ckicking on a “Forgot password?” button.
When this button is clicked, users are invited to enter their username or an email. If the provided username or the email correspond to an existing user, the system will provide a reset link to the configured email.
By clicking the link received by email the user is then invited to configure a new email different from the previous.

In case encryption is enabled on the system, a user clicking on the reset link would have first to insert the encryption-recovery-key and only in case of correct insertion the user will be enabled to set a new password.

In case 2FA is enabled on the system, a user clicking on the reset link would have first to insert an authentication code taken from the authentication API.

Entropy sources
---------------
The main source of entropy for the platform is /dev/urandom.

In order to increase the entropy available on the system the system integrates the usage of the haveged daemon:  http://www.issihosts.com/haveged/

Web application security
========================
This section describes the Web Application Security functionalities implemented by following the `OWASP REST Security Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html>`_.

Session management
------------------
The session implemenetation follows the `OWASP Session Management Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html>`_ security guidelines.

The system assigns a Session to each authenticated user.
The Session ID is 256bits long secret generated randomly by the backend.
Each session expire accordingly to a timeout of 5 minutes.
Session IDs are exchanged by the client with the backend by means of an header (X-Session) and do expire as soon that users close their browser or the tab running GlobaLeaks. Users could explicitly log out via a logout button or implicitly by closing the browser.

XSRF prevention
---------------
Cookies are not used intentionally to minimize any possible XSRF attack.

Input validation (backend)
--------------------------
The system adopts a whitelist based input validation approach. Each client request is checked against a set of regular expressions and only requests matching the expression are then processed.

As well a set of rules are applied to each request type to limit possible attacks. For example any request is limited to a payload of 1MB.

Input validation (client)
-------------------------
The client implement strict validation of the rendered content by using the angular component: http://docs.angularjs.org/api/ngSanitize.$sanitize

Security related HTTP headers
-----------------------------
Strict-Transport-Security
^^^^^^^^^^^^^^^^^^^^^^^^^
The system implements strict transport security by default.
::

  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

The preload feature is left optional to users and following the best practices is left disabled as default.

Content-Security-Policy
^^^^^^^^^^^^^^^^^^^^^^^
The backend implements the following content security policy (CSP):
::

  Content-Security-Policy: 'default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self' data:; font-src 'self' data:; img-src 'self' data:;

Feature-Policy
^^^^^^^^^^^^^^
The backend implements the following Feature-Policy header to limit the possible de-anonimization of the user by disabling dangerous browser features:
::

  Feature-Policy: camera 'none'; display-capture 'none'; document-domain 'none'; fullscreen 'none'; geolocation 'none'; microphone 'none; speaker 'none'

Referrer-Policy
^^^^^^^^^^^^^^^
Web-browsers usually attach referrers in their http headers as they browse links. The platform enforce a referrer policy to avoid this behaviour.
::

  Referrer-Policy: no-referrer

X-Content-Type-Options
^^^^^^^^^^^^^^^^^^^^^^
When setting up Content-Type for the specific output, we avoid the automatic mime detection logic of the browser by setting up the following header:
::

  X-Content-Type-Options: nosniff

X-XSS-Protection
^^^^^^^^^^^^^^^^
In addition in order to explicitly instruct browsers to enable XSS protections the Backend inject the following header:
::

  X-XSS-Protection: 1; mode=block

Crawlers Policy
^^^^^^^^^^^^^^^
In order to instruct crawlers to not index or cache platform data, the Backend injects the following HTTP header:
::

  X-Robots-Tag: noindex

Web Browser Privacy
-------------------
The Tor browser strives to remove as much identifiable information from requests as possible. It is still not perfect. For normal web browsers the situation is much more grave. The goals here are two: reduce the amount of application data and metadata stored on the a client’s machine, and reduce the amount of information about the client shared from client to backend.

Cache-control and other cache related headers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The Globaleaks backend by default sends the following headers to instruct client’s browsers to not store resources in their cache. For browsers that comply with the header and in Tor browser’s case this prevents resources served by the backend from reaching the disk via the client’s caching mechanism.
::

  Cache-control: no-cache, no-store, must-revalidate
  Pragma: no-cache
  Expires: -1

Anchor tags and external URLs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In order to guarantee user privacy has been given to the various ways a user may leave the application passing to a different external website leaking information about his operations. Keep the number of clickable external anchor tags to a minimum. The content generated by whistleblowers, recipients, and translators is strictly escaped to prevent the insertion of malicious links.

For links that point outward to external hosts the following safeguards are in place:
The HTML meta referrer is set to ‘never’:
::

   <meta name="referrer" content="never">

External url links provided by the Client include the following HTML5 tag to explicitly instruct the browser to avoid exposing HTTP referrer header:
<a href="https://external_url" rel="noreferrer">external_url</a>
Anchor tags with urls to other hosts with target=”_blank” use the  rel=”noopener” attribute. This works in some browsers (notably not FF or the TBB) to prevent the abuse window.opener in the new tab.

Cookies
-------
To prevent any potential abuse GlobaLeaks does not make use of any type of cookie.

Form autocomplete OFF (client)
------------------------------
Form implemented by the platform make use of the HTML5 form attribute in order to instruct the browser to do not keep caching of the user data in order to predict and autocomplete forms on subsequent submissions.

The implementation involve setting autocomplete=”false” on the relevant forms or attributes.

https://www.w3.org/TR/html5/forms.html=autofilling-form-controls:-the-autocomplete-attribute

Fonts
-----
The Client intentionally does not use any custom font not already included in the main operating systems and just use the following standard configuration:
::

  font-family: Helvetica, Arial, sans-serif

This choice consider to limit possible browser fingerprinting attacks.

Reference: https://panopticlick.eff.org/static/browser-uniqueness.pdf

Data encryption
===============
The data, files, messages and metadata exchanged between whistleblowers and recipients is encrypted using the GlobaLeaks :doc:`EncryptionProtocol`.
In addition to this GlobaLeaks implements many other encryption components and the following is the set of the main libraries and their main usage:

* `Python-NaCL <https://github.com/pyca/pynacl>`_: is used for implementing data encryption
* `PyOpenSSL <https://github.com/pyca/pyopenssl>`_: is used for implementing HTTPS
* `Python-Cryptography <https://cryptography.io>`_: is used for implementing authentication
* `Python-GnuPG <http://pythonhosted.org/python-gnupg/index.html>`_: is used for encrypting email notifications

DoS resiliency approach
=======================
To avoid applicative and database denial of service, GlobaLeaks apply the following measures:

It tries to limit the possibility of automating any operation by requiring human interaction (e.g. with the implementation of proof of work)
It is written to limit the possibility of triggering CPU intensive routines by an external user (e.g. by implementing limits on queries and jobs execution time)
It implements monitoring of each activity trying to implement detection of attacks and implement proactively security measures to prevent DoS (e.g. implementing slowdown on fast-operations)

Network sandboxing
==================
GlobaLeaks integrates iptables by default and implements by a strict firewall rule that only allow inbound and outbound connections from 127.0.0.1 (where Tor is running with Tor Hidden Service).

As well it automatically applies network sandboxing to all outbound communications that get automatically "torrified" (sent through Tor), being outbound TCP connections or DNS-query for name resolution.

The configuration of the network sandboxing is defined inside the init script of the application: https://github.com/globaleaks/GlobaLeaks/blob/master/debian/globaleaks.init

Application sandboxing
======================
GlobaLeaks integrates AppArmor by default and implements a strict sandboxing profile enabling the application to access only the strictly required files.
As well the application does run under a dedicated user and group "globaleaks" with reduced privileges.

The configuration of the network sandboxing is defined inside the init script of the application: https://github.com/globaleaks/GlobaLeaks/blob/master/debian/apparmor/usr.bin.globaleaks

Other measures
==============
Encryption of temporary files
-----------------------------
Files being uploaded and temporarily stored on the disk during the upload process are encrypted with a temporary, symmetric AES-key in order to avoid writing any part of an unencrypted file's data chunk to disk. The encryption is done in "streaming" by using AES 128bit in CTR mode. The key files are stored in memory and are unique for each file being uploaded.

Secure file delete
------------------
Every file deleted by the application if overwritten before releasing the file space on the disk.

The overwrite routine is performed by a periodic scheduler and acts as following:
A first overwrite writes 0 on the whole file;
A second overwrite writes 1 on the whole file;
A third overwrite writes random bytes on the whole file.

Secure deletion of database entries
-----------------------------------
The platform enables the sqlite capability for secure deletion that automatically makes the database overwrite the data upon each delete query.

Exception logging and redaction
-------------------------------
In order to quickly diagnose potential problems in the software when exceptions in clients are generated, they are automatically reported to the backend. The backend backend temporarily caches these exceptions and sends them to the backend administrator via email.

In order to prevent inadvertent information leaks the logs are run through filters that redact email addresses and uuids.

UUIDv4 Randomness
-----------------
Resources in the system like submissions and files are identified by a UUIDv4 in order to not be guessable by an external user and limit possible attacks.
The generation of UUIDv4 generation is enforced through the use of os.urandom.

TLS for SMTP Notification
-------------------------
All of the notifications are sent through SMTP over TLS encrypted channel by using SMTP/TLS or SMTPS, depending on the configuration.
