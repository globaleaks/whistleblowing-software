====================
Application Security
====================
The GlobaLeaks software tries to conform with industry standard best and practices and its security is a result of applied research.

This document try to detail every aspect implemented by the application in relation to the security design.

Architecture
============
GlobaLeaks is made up of two main software components: a ``Backend`` and a ``Client``:

* The Backend is a python backend that runs on a physical backend and exposes a ``REST API``
* The Client is a javascryipt client-side Web Application that interacts with Backend only through ``XHR``.

Authentication
==============
The confidentiality of the authentication is protected by either Tor Onion Services v3 or TLS version 1.2+

This section describes the authentication methods   implemented by the system.

Password
--------
By accessing the GlobaLeaks login interface, Administrators and Recipients need to insert their respective username and password. If the password submitted is valid, the system grants access to the functionality available to that user.

Receipt
-------
Whistleblowers access their Reports by using a Receipt, which is a randomly generated 16 digits sequence created by the Backend when the Report is first submitted. The reason of this format of 16 digits is that it resembles a standard phone number, making it easier for the whistleblower to conceal the receipt of their submission and give them plausible deniability on what is the significance of such digits.

Password Security
=================
The following password security measures implemented by the system.

Password Storage
----------------
Password are never stored in plaintext but the system maintain at rest only an hash. This apply to every authentication secret included whistleblower receipts.

The platform stores Users’ passwords hashed with a random 128 bit salt, unique for each user.

Passwords are hashed using `Argon2 <https://en.wikipedia.org/wiki/Argon2>`_, a key derivation function that was selected as the winner of the ``Password Hashing Competition`` in July 2015.

The hash involves a per-user salt for each user and a per-system salt for each whistleblower.

Password Complexity
-------------------
The system enforces the usage of complex password by implementing a custom algorithm necessary for ensuring a reasonable entropy of each authentication secret.

Password are scored in three levels: strong, acceptable, insecure.

* A strong password should be formed by capital letters, lowercase letters, numbers and a symbols, be at least 12 characters long and include a variety of at least 10 different inputs.
* An acceptable password should be formed by at least 3 different inputs over capital letters, lowercase letters, numbers and a symbols, be at least 10 characters and include a variety of at least 7 different inputs.

We encourage each end user to use `KeePassXC <https://keepassxc.org>`_ to generate and retain strong and unique passphrases.

Two Factor Authentication (2FA)
-------------------------------
The system implements Two Factor Authentication (2FA) based on TOTP based on `RFC 6238 <https://tools.ietf.org/rfc/rfc6238.txt>`_ alghorithm and 160 bits secrets.

Users are enabled to enroll for Two Factor Authentication via their own preferences and administrators can optionally enforce this requirement.

We recommend using FreeOTP available `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`_ and `for iOS <https://apps.apple.com/us/app/freeotp-authenticator/id872559395>`_.
------------------------------
The system enforces users to change their own password at their first login.

Administrators could as well enforce password change for users at their next login.

Periodic Password Change
------------------------
By default the system enforces users to change their own password at least every year.

This period is configurable by administrators.

Proof of Work on Login and Submissions
--------------------------------------
The system implements an automatic ``proof of work`` on every login that requires every client to request a token, solve a computational probelm before being able to perform a login or file a submission.

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

In case 2FA is enabled on the system, a user clicking on the reset link would have first to insert an authentication code taken from the authentication API.

Web Application Security
========================
This section describes the Web Application Security implemented by the software in adherence with the `OWASP Security Guidelines <https://www.owasp.org>`_.

Session management
------------------
The session implemenetation follows the `OWASP Session Management Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html>`_ security guidelines.

The system assigns a Session to each authenticated user. The Session ID is 256bits long secret generated randomly by the backend. Each session expire accordingly to a timeout of 5 minutes. Session IDs are exchanged by the client with the backend by means of an header (X-Session) and do expire as soon that users close their browser or the tab running GlobaLeaks. Users could explicitly log out via a logout button or implicitly by closing the browser.

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

The preload feature is left optional to users and following the best practices is left disabled as default.

Content-Security-Policy
+++++++++++++++++++++++
The backend implements the following Content Security Policy (CSP):
::
  Content-Security-Policy: default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; media-src 'self'; form-action 'self'; frame-ancestors 'none'; block-all-mixed-content

Permissions-Policy
++++++++++++++
The backend implements the following Permissions-Policy header configuration to limit the possible de-anonimization of the user by disabling dangerous browser features:
::
  Permissions-Policy: camera=('none') display-capture=('none') document-domain=('none') fullscreen=('none') geolocation=('none') microphone=('none') speaker=('none')

X-Frame-Options
+++++++++++++++
The backend configure the X-Frame-Options header to prevent inclusion by means of Iframes in any site:
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

X-XSS-Protection
++++++++++++++++
In addition in order to explicitly instruct browsers to enable XSS protections the Backend inject the following header:
::
  X-XSS-Protection: 1; mode=block

Cache-Control
+++++++++++++++++++++++++++++++++++++++++++++
The backend by default sends the following headers to instruct client’s browsers to not store resources in their cache.
As by section ``3. Storing Responses in Caches`` of `RFC 7234 <https://tools.ietf.org/html/rfc7234>`_ the platform uses the ``Cache-control`` HTTP header with the configuration ``no-store`` not instruct clients to store any entry to be used for caching; this settings make it not necessary to use any other headers like ``Pragma`` and ``Expires``.
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

For high sensitive projects where the platform is inteded to remain ``hidden`` and commuicated to possible whistleblowers directly the platform could be as well configured to disable indexing completely.

The following is the HTTP header injected in this case:
::
  X-Robots-Tag: noindex

Anchor Tags and External URLs
-----------------------------
In addition to the protecton offered by the header ``Referrer-Policy: no-referrer`` that prevents to pass the referrer while visiting the application sets the rel attribute nooopener to each of the external links. This protects from exectution of malicious content within the context of the application.
::
  <a href="url" rel="noopener">link title</a>

Input Validation (Server)
-------------------------
The system adopts a whitelist based input validation approach. Each client request is checked against a set of regular expressions and only requests matching the expression are then processed.

As well a set of rules are applied to each request type to limit possible attacks. For example any request is limited to a payload of 1MB.

Input Validation (Client)
-------------------------
The client implement strict validation of the rendered content by using the angular component `ngSanitize.$sanitize <http://docs.angularjs.org/api/ngSanitize.$sanitize>`_

Form Autocomplete OFF
---------------------
Form implemented by the platform make use of the HTML5 form attribute in order to instruct the browser to do not keep caching of the user data in order to predict and autocomplete forms on subsequent submissions.

This is achieved by setting `autocomplete=”false” <https://www.w3.org/TR/html5/forms.html=autofilling-form-controls:-the-autocomplete-attribute>`_ on the relevant forms or attributes.

Network Security
================

Connection Encryption
---------------------
The software adopts `Tor <https://www.torproject.org/>`_ as default, prefferred and recommended connection encryption protocol for its security and each GlobaLeaks server by default implement an ``Onion Service v3``.
The use of ``Tor`` is recommended over HTTPS for its advanced properties of resistance to selective interception and censorship that would make it difficult for a third party to selectively capture or block tccess to the site to specific whistleblower or company department.

The software enables as well easy setup of ``HTTPS`` offering both automatic setup via `Let'sEncrypt <https://letsencrypt.org/>`_ and manual setup.

The configuration enables only ``TLS1.2+`` and is fine tuned and hardened to achieve `SSLLabs grade A+ <https://www.ssllabs.com/ssltest/analyze.html?d=try.globaleaks.org>`_.

In particular only following cyphertexts are enabled:
::
  TLS13-AES-256-GCM-SHA384
  TLS13-AES-128-GCM-SHA256
  TLS13-CHACHA20-POLY1305-SHA256
  ECDHE-ECDSA-AES256-GCM-SHA384
  ECDHE-RSA-AES256-GCM-SHA384
  ECDHE-ECDSA-AES128-GCM-SHA256
  ECDHE-RSA-AES128-GCM-SHA256
  ECDHE-ECDSA-CHACHA20-POLY1305
  ECDHE-RSA-CHACHA20-POLY1305

Network Sandboxing
------------------
The GlobaLeaks backend integrates ``iptables`` by default and implements strict firewall rules that only allow inbound and outbound connections from 127.0.0.1 (where Tor is running with Tor Onion Service).

As well it automatically applies network sandboxing to all outbound communications that get automatically ```torrified``` (sent through Tor), being outbound TCP connections or DNS-query for name resolution.

Data Encryption
===============
The data, files, messages and metadata exchanged between whistleblowers and recipients is encrypted using the GlobaLeaks :doc:`EncryptionProtocol`.
In addition to this GlobaLeaks implements many other encryption components and the following is the set of the main libraries and their main usage:

* `Python-NaCL <https://github.com/pyca/pynacl>`_: is used for implementing data encryption
* `PyOpenSSL <https://github.com/pyca/pyopenssl>`_: is used for implementing HTTPS
* `Python-Cryptography <https://cryptography.io>`_: is used for implementing authentication
* `Python-GnuPG <http://pythonhosted.org/python-gnupg/index.html>`_: is used for encrypting email notifications

Application Sandboxing
======================
The GlobaLeaks backend integrates ``AppArmor`` by default and implements a strict sandboxing profile enabling the application to access only the strictly required files.
As well the application does run under a dedicated user and group "globaleaks" with reduced privileges.

DoS Resiliency
==============
To avoid applicative and database denial of service, GlobaLeaks apply the following measures:

* It tries to limit the possibility of automating any operation by requiring human interaction (e.g. with the implementation of proof of work)
* It is written to limit the possibility of triggering CPU intensive routines by an external user (e.g. by implementing limits on queries and jobs execution time)
* It implements monitoring of each activity trying to implement detection of attacks and implement proactively security measures to prevent DoS (e.g. implementing slowdown on fast-operations)

Other Measures
==============
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

Secure Deletion of Database Entries
-----------------------------------
The platform enables the SQLite capability for secure deletion that automatically makes the database overwrite the data upon each delete query:
::
  PRAGMA secure_delete = ON
  PRAGMA auto_vacuum = FULL

Exception Logging and Redaction
-------------------------------
In order to quickly diagnose potential problems in the software when exceptions in clients are generated, they are automatically reported to the backend. The backend backend temporarily caches these exceptions and sends them to the backend administrator via email.

In order to prevent inadvertent information leaks the logs are run through filters that redact email addresses and uuids.

Entropy Sources
---------------
The main source of entropy for the platform is ``/dev/urandom``.

In order to increase the entropy available on the system the system integrates the usage of the `Haveged <http://www.issihosts.com/haveged/>`_ daemon.

UUIDv4 Randomness
-----------------
Resources in the system like submissions and files are identified by a UUIDv4 in order to not be guessable by an external user and limit possible attacks.

TLS for SMTP Notification
-------------------------
All of the notifications are sent through SMTP over TLS encrypted channel by using SMTP/TLS or SMTPS, depending on the configuration.
