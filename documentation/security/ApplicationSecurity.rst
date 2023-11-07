====================
Application Security
====================
The GlobaLeaks software tries to conform with industry standard best and practices and its security is a result of applied research.

This document tries to detail every aspect implemented by the application in relation to the security design.

Architecture
============
The software is made up of two main components: a ``Backend`` and a ``Client``:

* The Backend is a python backend that runs on a physical backend and exposes a `REST API <https://en.wikipedia.org/wiki/Representational_state_transfer>`_.
* The Client is a JavaScript client-side web application that interacts with Backend only through `XHR <https://en.wikipedia.org/wiki/XMLHttpRequest>`_.

Anonymity
=========
Users's anonymity is protected by means of the `Tor <https://www.torproject.org>`_ technology.

The entire application considers to avoid logging of sensible metadata that could lead to identification of whistleblowers.

Authentication
==============
The confidentiality of the authentication is protected by either `Tor Onion Services v3 <https://www.torproject.org/docs/onion-services.html.en>`_ or `TLS version 1.2+ <https://en.wikipedia.org/wiki/Transport_Layer_Security>`_.

This section describes the authentication methods implemented by the system.

Password
--------
By accessing the login web interface, ``Administrators`` and ``Recipients`` need to insert their respective ``Username`` and ``Password``. If the password submitted is valid, the system grants access to the functionality available to that user.

Receipt
-------
``Whistleblowers`` access their ``Reports`` by using an anonymous ``Receipts``, which are random generated 16 digits sequences created by the Backend when the Report is first submitted. The reason of this format of 16 digits is that it resembles a standard phone number, making it easier for the whistleblowers to conceal their receipts.

Password Security
=================
The following password security measures implemented by the system.

Password Storage
----------------
Password are never stored in plaintext but the system maintain at rest only an hash. This apply to every authentication secret included whistleblower receipts.

The platform stores Users’ passwords hashed with a random 128 bit salt, unique for each user.

Passwords are hashed using `Argon2 <https://en.wikipedia.org/wiki/Argon2>`_, a key derivation function that was selected as the winner of the `Password Hashing Competition <https://en.wikipedia.org/wiki/Password_Hashing_Competition>`_ in July 2015.

The hash involves a per-user salt for each user and a per-system salt for whistleblowers.

Password Complexity
-------------------
The system enforces the usage of complex password by implementing a custom algorithm necessary for ensuring a reasonable entropy of each authentication secret.

Password are scored in three levels: ``Strong``, ``Acceptable``, ``Insecure``.

* Strong: A strong password should be formed by capital letters, lowercase letters, numbers and a symbols, be at least 12 characters long and include a variety of at least 10 different inputs.
* Acceptable: An acceptable password should be formed by at least 3 different inputs over capital letters, lowercase letters, numbers and a symbols, be at least 10 characters and include a variety of at least 7 different inputs.
* Insecure: A password ranked below the strong or acceptable levels is marked as insecure and not accepted by the system.

We encourage each end user to use `KeePassXC <https://keepassxc.org>`_ to generate and retain strong and unique passphrases.

Two Factor Authentication
-------------------------
The system implements Two Factor Authentication (2FA) based on ``TOTP`` based on `RFC 6238 <https://tools.ietf.org/rfc/rfc6238.txt>`_ algorithm and 160 bits secrets.

Users are enabled to enroll for 2FA via their own preferences and administrators can optionally enforce this requirement.

We recommend using `FreeOTP <https://freeotp.github.io/>`_ available `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`_ and `for iOS <https://apps.apple.com/us/app/freeotp-authenticator/id872559395>`_.

Password Change on First Login
------------------------------
The system enforces users to change their own password at their first login.

Administrators could as well enforce password change for users at their next login.

Periodic Password Change
------------------------
By default the system enforces users to change their own password at least every year.

This period is configurable by administrators.

Proof of Work on Login and Submissions
--------------------------------------
The system implements an automatic `Proof of Work <https://en.wikipedia.org/wiki/Proof_of_work>`_ on every login that requires every client to request a token, solve a computational problem before being able to perform a login or file a submission.

Rate Limit on Anonymous Sessions
--------------------------------
The system implements rate limiting on whistleblowers' sessions preventing to execute more than 5 requests per second.

Slowdown on Failed Login Attempts
---------------------------------
The system identifies multiple failed login attempts and implement a slowdown procedure where an authenticating client should wait up to 42 seconds to complete an authentication.

This feature is intended to slow down possible attacks requiring more resources to users in terms of time, computation and memory.

Password Recovery
-----------------
In case of password loss users could request a password reset via the web login interface clicking on a ``Forgot password?`` button present on the login interface.

When this button is clicked, users are invited to enter their username or an email. If the provided username or the email correspond to an existing user, the system will provide a reset link to the configured email.

By clicking the link received by email the user is then invited to configure a new email different from the previous.

In case encryption is enabled on the system, a user clicking on the reset link would have first to insert their ``Account Recovery Key`` and only in case of correct insertion the user will be enabled to set a new password.

Web Application Security
========================
This section describes the Web Application Security implemented by the software in adherence with the `OWASP Security Guidelines <https://www.owasp.org>`_.

Session Management
------------------
The session implementation follows the `OWASP Session Management Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html>`_ security guidelines.

The system assigns a Session to each authenticated user. The Session ID is 256bits long secret generated randomly by the backend. Each session expire accordingly to a timeout of 60 minutes. Session IDs are exchanged by the client with the backend by means of an header (``X-Session``) and do expire as soon that users close their browser or the tab running GlobaLeaks. Users could explicitly log out via a logout button or implicitly by closing the browser.

Cookies and XSRF Prevention
---------------------------
Cookies are not used intentionally to minimize XSRF attacks and any possible attack based on them. Instead than using Cookies authentication is based on a custom HTTP Session Header sent by the client on authenticated requests.

HTTP Headers
------------
The system implements a large set of HTTP headers specifically configured to improve the software security and achieves `score A+ <https://securityheaders.com/?q=https%3A%2F%2Ftry.globaleaks.org&followRedirects=on>`_ by `Security Headers <https://securityheaders.com/>`_ and `score A+ <https://observatory.mozilla.org/analyze/try.globaleaks.org>`_ by `Mozilla Observatory <https://observatory.mozilla.org/>`_.

Strict-Transport-Security
+++++++++++++++++++++++++
The system implements strict transport security by default.
::
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

The default configuration of the application see this feature disabled.

Content-Security-Policy
+++++++++++++++++++++++
The backend implements a strict `Content Security Policy (CSP) <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>`_ preventing any interaction with resources of third parties and restricting execution of untrusted user input:
::
  Content-Security-Policy: base-uri 'none'; default-src 'none'; form-action 'none'; frame-ancestors 'none'; sandbox;

On this default policy are then implemented specific policies in adherence to the principle of least privilege.

For example:

* the index.html source of the app is the only resource enabled to load scripts from the same origin;
* every dynamic content is strictly sandboxed on a null origin;
* every untrusted user input or third party library is executed in a sandbox limiting its interaction with other application components.

Cross-Origin-Embedder-Policy
++++++++++++++++++++++++++++
The backend implements the following `Cross-Origin-Embedder-Policy (COEP) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Embedder-Policy>`_:
::
  Cross-Origin-Embedder-Policy: require-corp

Cross-Origin-Opener-Policy
++++++++++++++++++++++++++
The backend implements the following `Cross-Origin-Opener-Policy (COOP) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Opener-Policy>`_:
::
  Cross-Origin-Resource-Policy: same-origin

Cross-Origin-Resource-Policy
++++++++++++++++++++++++++++
The backend implements the following `Cross-Origin-Resource-Policy (CORP) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Cross-Origin_Resource_Policy>`_:
::
  Cross-Origin-Resource-Policy: same-origin

Permissions-Policy
++++++++++++++
The backend implements the following Permissions-Policy header configuration to limit the possible de-anonymization of the user by disabling dangerous browser features:
::
  Permissions-Policy: camera=() display-capture=() document-domain=() fullscreen=() geolocation=() microphone=() serial=() usb=() web-share=()

X-Frame-Options
+++++++++++++++
In addition to the implemtent Content Security Policy of level 3 that prevent the application to be included into an Iframe, the backend implements the outdated X-Frame-Options header to enure that iframes are always prevented in any circumstance also on outdated browsers:
::
  X-Frame-Options: deny

Referrer-Policy
+++++++++++++++
Web-browsers usually attach referrers in their http headers as they browse links. The platform enforce a referrer policy to avoid this behaviour.
::
  Referrer-Policy: no-referrer

X-Content-Type-Options
++++++++++++++++++++++
When setting up Content-Type for the specific output, we avoid the automatic mime detection logic of the browser by setting up the following header:
::
  X-Content-Type-Options: nosniff

Cache-Control
+++++++++++++
To prevent or limit the the forensic traces left on the device used by whistleblowers and in the devices involved in the communication the platform, as by section ``3. Storing Responses in Caches`` of `RFC 7234 <https://tools.ietf.org/html/rfc7234>`_ the platform uses the ``Cache-control`` HTTP header with the configuration ``no-store`` to instruct clients and possible network proxies to disable any sort of data cache.
::
  Cache-Control: no-store

Crawlers Policy
------------
For security reasons the backend instructs crawlers to avoid any caching and indexing of the application and uses the ``Robots.txt`` file to enable crawling only of the home page; indexing of the home page is in fact considered best practice in order to be able to widespread the information about the existance of the platform and ease access to possible whistleblowers.

The configuration implemented is the following:
::
  User-agent: *
  Allow: /$
  Disallow: *

As well the platform instruct crawlers to not keep any cache by injecting the following HTTP header:
::
  X-Robots-Tag: noarchive

For high sensitive projects where the platform is intended to remain ``hidden`` and communicated to possible whistleblowers directly the platform could be as well configured to disable indexing completely.

The following is the HTTP header injected in this case:
::
  X-Robots-Tag: noindex

Anchor Tags and External URLs
-----------------------------
The client opens external urls on a new tab independent from the application context by setting ``rel='noreferrer'`` and ``target='_blank'``` on every anchor tag.
::
  <a href="url" rel="noreferrer" target="_blank">link title</a>

Input Validation
----------------
The application implement strict input validation both on the backend and on the client

On the Backend
++++++++++++++
Each client request is strictly validated by the backend against a set of regular expressions and only requests matching the expression are then processed.

As well a set of rules are applied to each request type to limit possible attacks. For example any request is limited to a payload of 1MB.

On the Client
+++++++++++++
Each server output is strictly validated by the Client at rendering time by using the angular component `ngSanitize.$sanitize <http://docs.angularjs.org/api/ngSanitize.$sanitize>`_

Form Autocomplete OFF
---------------------
Form implemented by the platform make use of the HTML5 form attribute in order to instruct the browser to do not keep caching of the user data in order to predict and autocomplete forms on subsequent submissions.

This is achieved by setting `autocomplete=”off” <https://www.w3.org/TR/html5/forms.html=autofilling-form-controls:-the-autocomplete-attribute>`_ on the relevant forms or attributes.

Network Security
================
Connection Anonymity
--------------------
Users's anonymity is offered by means of the implementation of the `Tor <https://www.torproject.org/>`_ technology. The application implements an ``Onion Service v3`` and advices users to use the Tor Browser when accessing to it.

Connection Encryption
---------------------
Users' connection is always encrypted, by means of the `Tor Protocol <https://www.torproject.org>`_ while using the Tor Browser or by means of `TLS <https://en.wikipedia.org/wiki/Transport_Layer_Security>`_ when the application is accessed via a common browser.

The use of the ``Tor`` is recommended over HTTPS for its advanced properties of resistance to selective interception and censorship that would make it difficult for a third party to selectively capture or block access to the site to specific whistleblower or company department.

The software enables as well easy setup of ``HTTPS`` offering both automatic setup via `Let'sEncrypt <https://letsencrypt.org/>`_ and manual setup.

TLS Certificates are generated using using `NIST Curve P-384 <https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf>`_.

The configuration enables only ``TLS1.2+`` and is fine tuned and hardened to achieve `SSLLabs grade A+ <https://www.ssllabs.com/ssltest/analyze.html?d=try.globaleaks.org>`_.

In particular only following ciphertexts are enabled:
::
  TLS13-AES-256-GCM-SHA384
  TLS13-CHACHA20-POLY1305-SHA256
  TLS13-AES-128-GCM-SHA256
  ECDHE-ECDSA-AES256-GCM-SHA384
  ECDHE-RSA-AES256-GCM-SHA384
  ECDHE-ECDSA-CHACHA20-POLY1305
  ECDHE-RSA-CHACHA20-POLY1305
  ECDHE-ECDSA-AES128-GCM-SHA256
  ECDHE-RSA-AES128-GCM-SHA256

Network Sandboxing
-------------------
The GlobaLeaks backend integrates `iptables <https://www.netfilter.org/>`_ by default and implements strict firewall rules that restrict network incoming network connection to HTTP and HTTPS connection on ports 80 and 443.

In addition the application makes it possible to anonymize outgoing connections that could be configured to be sent through Tor.

Data Encryption
===============
Submissions data, file attachment, messages and metadata exchanged between whistleblowers and recipients is encrypted using the GlobaLeaks :doc:`EncryptionProtocol`.

In addition to this GlobaLeaks implements many other encryption components and the following is the set of the main libraries and their main usage:

* `Python-NaCL <https://github.com/pyca/pynacl>`_: is used for implementing data encryption
* `PyOpenSSL <https://github.com/pyca/pyopenssl>`_: is used for implementing HTTPS
* `Python-Cryptography <https://cryptography.io>`_: is used for implementing authentication
* `Python-GnuPG <http://pythonhosted.org/python-gnupg/index.html>`_: is used for encrypting email notifications and file downloads by means of ```PGP```

Application Sandboxing
======================
The GlobaLeaks backend integrates `AppArmor <https://apparmor.net/>`_ by default and implements a strict sandboxing profile enabling the application to access only the strictly required files.
As well the application does run under a dedicated user and group "globaleaks" with reduced privileges.

Database Security
=================
The GlobaLeaks backend implements an hardened local SQLite database accessed via the SQLAlchemy ORM.

This design choice is selected in order to ensure that the application could fully control its configuration implementing a large set of security measures in adhrerence to the `security recomendations by  SQLite <https://sqlite.org/security.html>`_

Secure Deletion
---------------
The GlobaLeaks backend enables a SQLite capability for secure deletion that automatically makes the database overwrite the data upon each delete query:
::
  PRAGMA secure_delete = ON

Auto Vacuum
-----------
The platform enables a SQLite capability for automatic vacuum of deleted entries with automatic recall of unused pages:
::
  PRAGMA auto_vacuum = FULL

Limited Database Trust
----------------------
The GlobaLeaks backend utilizes the SQLite `trusted_schema <https://www.sqlite.org/src/doc/latest/doc/trusted-schema.md>`_ pragma to limit the trust put on the database in order to limit exploitation on which the database could be maliciously corrupted by an attacker.
::
  PRAGMA trusted_schema = OFF

Limited Database Functionalities
--------------------------------
The GlobaLeaks backend runs specific SQLite functionalities to reduce the types of queries to the ones necessary to run the application and reduce the possibilities of explotation in case of successfull SQL injection attacks.

This is implemented by using the ```conn.set_authorizer``` API and using a strict authorizer callback that authorizes the execution of a limited set of SQL instructions:
::
  SQLITE_FUNCTION: count, lower, min, max
  SQLITE_INSERT
  SQLITE_READ,
  SQLITE_SELECT
  SQLITE_TRANSACTION
  SQLITE_UPDATE

DoS Resiliency
==============
To avoid applicative and database denial of service, GlobaLeaks apply the following measures:

* It tries to limit the possibility of automating any operation by implement a proof of work on each unauthenticared request (hashcash)
* It applies rete limiting on any authenticated session
* It is written to limit the possibility of triggering CPU intensive routines by an external user (e.g. by implementing limits on queries and jobs execution time)
* It implements monitoring of each activity trying to implement detection of attacks and implement proactively security measures to prevent DoS (e.g. implementing slowdown on fast-operations)

Other Measures
==============
Browser History and Forensic Traces
-----------------------------------
The whole application is designed keeping in mind to try to avoid or reduce the forensic traces left by whistleblowers on their devices while filing their reports.

When the accessed via the Tor Browser, the browser guarantees that no persistent traces are left on the device of the user.

In order to prevent or limit the forensic traces left in the browser history of the users accessing the platform via a common browser, the application avoids to change URI during whistleblower navigation. This has the effect to prevent the browser to log the activities performed by the user and offers high plausible deniability protection making the whistleblower appear as a simple visitor of the homepage and avoiding an actual evidence of any submission.

Secure File Management
----------------------
Secure File Download
++++++++++++++++++++
Any attachment file uploaded by anonymous whistleblowers could possibly contain malware that could be provided intentionally or not. It is always recommended if possible to download files and access them on an air-gapped machine disconnected from the network and other sensible devices. In order to safely downlod files and move them using a USB stick the application offers the possibility to perform a report export enabling the download of a ZIP archive including all the report content and thus reducing risks of executing files on-click during the file transfer from a device to one other.

Safe File Opening
+++++++++++++++++
For conditions where the whistleblower trustworthines has been validated or in projects subject to a low risk threat model, the application offers an integrated file viewer that benefiting of modern browser sandboxing capabilities enable opening of a limited set of file types that are considered more safe and in a way that is better than accessing files directly through the operation system.
This option is disabled by default and it is recommended that administrators of the project enable this feature only after proper evaluation and only in conditions in which it possible to ensure that recipients' browsers are always maintained up-to-date.
Among the advantages of this novel viewer is the fact that access to files is performed within a controlled sandbox, via a set of controlled libraries and avoiding usage of any permanent storage and thus limiting the the exposure of the opened file.

The set of file formats supported by this viewer are:

* AUDIO
* CSV
* IMAGE
* PDF
* VIDEO
* TXT

The default configuration of the application see this feature disabled.

PGP Encryption
++++++++++++++
The system offers an optional PGP encryption feature.

When enabled, users could possibly enable a personal PGP key that will be used by the system to encrypt email notifications and encrypt downloaded files on-the-fly.

This is a recommended feature for high risk threat models in association with the usage of air-gapped systems for the visualization of the reports.

The default configuration of the application see this feature disabled.

Encryption of Temporary Files
-----------------------------
Files being uploaded and temporarily stored on the disk during the upload process are encrypted with a temporary, symmetric AES-key in order to avoid writing any part of an unencrypted file's data chunk to disk. The encryption is done in "streaming" by using ``AES 128bit`` in ``CTR mode``. The key files are stored in memory and are unique for each file being uploaded.

Secure File Delete
------------------
Every file deleted by the application if overwritten before releasing the file space on the disk.

The overwrite routine is performed by a periodic scheduler and acts as following:

* A first overwrite writes 0 on the whole file;
* A second overwrite writes 1 on the whole file;
* A third overwrite writes random bytes on the whole file.

Exception Logging and Redaction
-------------------------------
In order to quickly diagnose potential problems in the software when exceptions in clients are generated, they are automatically reported to the backend. The backend backend temporarily caches these exceptions and sends them to the backend administrator via email.

In order to prevent inadvertent information leaks the logs are run through filters that redact email addresses and uuids.

Entropy Sources
---------------
The main source of entropy for the platform is ``/dev/urandom``.

UUIDv4 Randomness
-----------------
Resources in the system like submissions and files are identified by a UUIDv4 in order to not be guessable by an external user and limit possible attacks.

TLS for SMTP Notification
-------------------------
All of the notifications are sent through SMTP over TLS encrypted channel by using SMTP/TLS or SMTPS, depending on the configuration.
