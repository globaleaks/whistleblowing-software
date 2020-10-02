============
Threat Model
============
GlobaLeaks is an Open Whistleblowing Framework that can be used in many different usage scenarios that may require very different approaches to obtain both security and flexibility.
Whistleblowing policies and procedures within a corporation for compliance purposes are reasonably different from the ones of a Media outlet or the ones for Hacktivism initiatives.
Given the flexibility of uses of GlobaLeaks, the threat model considers different usage scenarios as threats can vary.

Actors Matrix
=============
As a first step we define the actors, that are the users that interact with a GlobaLeaks platform.

.. csv-table::
   :header: "Actor", "Definition"

   "Whistleblower", "The user that submit an anonymous report through the GlobaLeaks platform. Whistleblower be persons in a wide range of different threat models depending on the usage scenario and the sensibility of information being submitted."
   "Recipient", "The user (person or organization) receiving the anonymous report submitted by the Whistleblower. The recipient acts reasonably in good faith, e.g. if either of them were to give their credentials or private information to the attacker that would be unreasonable."
   "Administrator", "The user (person or organization) that is running the GlobaLeaks platform. Administrator may not represent the same entity running, promoting and managing the whistleblowing initiatives (e.g., hosted solutions, multiple stakeholders projects, etc). The Administrator has to be considered in all scenarios described as a trusted entity with reference to the data exchanged by actors. The Administrator in most scenarios won’t be a trusted entity with respect to the identity of actors."

It’s highly relevant to apply each of the security measures always in relationship to the actors using GlobaLeaks, while always considering the security and usability tradeoff.

Anonymity Matrix
================
The anonymity of different actors must be differentiated and requires to be classified depending on the context of use represented by the following definitions:

.. csv-table::
   :header: "Actor", "Definition"

   "Anonymous", "Actors identity and their location cannot be disclosed."
   "Confidential", "The system is designed to remove or limit any recording of identifiable information that when registered is maintained encrypted and managed confidentially."

The following matrix relates the previous definition to different architectural use and implementation of GlobaLeaks software:

.. csv-table::

   "Recipient", "Anonymous", "Confidential"
   "Whistleblower", "Anonymous", "Confidential"
   "Administrator", "Anonymous", "Confidential"

Different use of GlobaLeaks require to consider the requirements for different actors in the anonymity matrix. The Anonymity level is reported on the user interface with the aim to make the user aware of it. The Administrator can configure the Anonymity level required for each actor.

Communication Security Matrix
=============================
The security of communication in respect to third parties transmission's monitoring may have different requirements depending on its context of use.

.. csv-table::
   "High security", "The communication is encrypted end-to-end with the GlobaLeaks platform and no third party is in a condition to eavesdrop the communication."
   "Medium security", "The communication is encrypted end-to-end with the GlobaLeaks platform. A third party able to manipulate HTTPS security (e.g., Govt re-issuing TLS cert) is in a condition to eavesdrop the communication. If HTTPS security is guaranteed, Monitoring  actor’s communication’s line or the GlobaLeaks platform communication’s line is not possible."
   "No security", "The communication is not encrypted at all. Monitoring the communication’s line of the actor or of the GlobaLeaks platform is possible."

The following matrix applies the previous definition related to different architectural implementations of GlobaLeaks software:

.. csv-table::
   :header: "Communication security matrix", "Tor", "HTTPS"

   "Security Level", "High security", "Medium security"

Identity Disclosure Matrix
==========================
Regardless from the anonymity matrix, various actors may be in a condition to decide to, or get mandated to disclose or not disclose their identity.

.. csv-table::

   "Undisclosed", "The actor identity is not disclosed and its disclosure is not likely."
   "Partially disclosed (pseudonym)", The actor operate under a pseudonym while interacting with the platform."
   "Optionally disclosed", "The actor’s identity is by default not disclosed, but he is given the chance to disclose it on a voluntary basis (e.g., in some workflow an anonymous tip-off may receive a follow-up, while a formal report with identity disclosed must receive a follow-up)"
   "Disclosed", "The actor who decided to, or get mandated to, disclose its identity to other actors."

Identity disclosure is a highly relevant topic, because even in an Anonymous High security environment the Identity disclosure may be an Option for specific whistleblowing initiatives workflows.

If an actor starts dealing with an Anonymity set “Anonymous” and with an “Undisclosed Identity” he can always decide, at a later stage, to disclose their identity. The opposite is not possible.
This is one of the key elements to provide actors’ protection around GlobaLeaks.

The voluntary identity disclosure may be required in certain whisteblowing procedures because, generally:
* Tip off MAY receive a follow-up and can be anonymous;
* Formal reports MUST receive a follow-up and in that case cannot be anonymous.

The “MAY” vs. “MUST” respect to the actions of recipients is a fundamental element of guarantee for many whistleblowing initiatives (e.g., a corporate or institutional whistleblowing platform, should not follow a MUST approach for Anonymous submission, considering them just tip-off and not formal reports). 
Usage Scenarios matrix
In this section you will find a set of examples that show how different anonymity level of different actors can be mixed together depending on the context of use.

.. csv-table::

   "Media outlet", "A Media outlet, whose identity is disclosed, decides starting a Whistleblowing initiative. The media’s recipients are disclosed to Whistleblowers, so that they can trust a specific journalist rather than the media itself. Full anonymity must be assured to whistleblowers and their identity cannot be disclosed in connection with anonymous submissions. The whistleblower MAY choose to willingly disclose identity (journalist had in their goals to protect source in some countries)"
   "Corporate compliance", "A Corporation needs to implement transparency, or anti-bribery law compliance, by promoting its initiatives to employees, consultants and providers. The recipients are partially disclosed because they are represented by different divisions of the “Internal Audit” business unit of the company. The Whistleblower is guaranteed full anonymity, but he can optionally disclose their identity (tip off vs formal report)."
   "Government tax whistleblowing", "A Government Authority (central or local) with its own public identity wants to promote Tax Whistleblowing with Rewards procedures for Whistleblowers (e.g., IRS). The recipients are not known because they are an internal division not exposing their names to the Whistleblower in advance. The Whistleblower MUST disclose their identity in order to be eligible for rewards."
   "Human Rights Activism Initiative", "A Human Rights Group start a Whistleblowing initiative to spot human rights violations in a dangerous place. The organization requires anonymity to avoid retaliations and takedowns, and operates under a Pseudonym. The Recipients MUST not be disclosed to the Whistleblowers, but a Partial Disclosure by pseudonym can be acceptable in order to give proper trust to “Who the whistleblower is submitting to” . The Whistleblower MUST be guaranteed anonymity and their identity cannot be disclosed."
   "Citizen media initiative", "A Citizen media initiative with it’s own public identity wants to collect tips on a specific topic (political, environmental malpractice, corruption, etc) in a medium-low risk operational context. The recipients must be disclosed but using a Pseudonym in order to avoid giving them too much responsibility, while accepting a Confidential relationship with no anonymity. The Whistleblower, if the topic is not life-threatening, can be allowed to submit also in a Confidential way to lower the entrance barrier."
   "Public Agency Iniziative", "A local public agency wants to setup a Street Hole Reporting service with it’s own public identity. The recipient can be disclosed to facilitate the CRM (Citizen relationship management) and Whistleblower identity protection is not required."

GlobaLeaks Security Matrix
==========================
Below we show how different usage scenarios can require different set of anonymity level, communication security requirements and identity disclosures for different actors.

Globaleaks, through its user interface, will enable each actor with appropriate security awareness information, and will enforce specific requirements to specific actors by the application of clear configuration guidelines.

.. csv-table::
   :header: "Scenario", "Actor", "Anonymity level", "Identity disclosure", "Communication security"

   "Media outlet", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "No anonymity", "Disclosed", "Medium security"
   "", "Admin", No anonymity", "Disclosed", "Medium security"
   "", "", "", "", ""
   "Corporate compliance", "Whistleblower", Anonymous", "Optionally disclosed", "High security"
    "", "Recipient", "No anonymity", "Partially disclosed", "Medium security"
    "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "", "", "", "", ""
   Government tax whistleblowing", "Whistleblower", "No anonymity", "Disclosed", "Medium security"
   "", "Recipient", "No anonymity", "Undisclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "", "", "", "", ""
   "Human Rights Activism initiative", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "Anonymous", "Partially disclosed", "High security"
   "", "Admin", "Anonymous", "Partially disclosed", "High security"
   "", "", "", "", ""
   "Citizen media initiative", "Whistleblower", "Confidential", "Optionally disclosed", "Medium security"
   "", "Recipient", "Confidential", "Confidential", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "", "", "", "", ""
   "Public agency initiative", "Whistleblower", "No anonymity", "Optionally disclosed", "No security"
   "", "Recipient", "No anonymity", "Undisclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"

The previous schema gives only some examples of GlobaLeaks’s flexibility; but different anonymity, identity and security measures apply to other usage scenarios and actors.

Data Security Matrix
====================
This section highlights the data that is handled by GlobaLeaks software and how different protection schemes are applied to GlobaLeaks handled data.

The following data are the one involved within GlobaLeaks:

.. csv-table::
   :header: "Data", "Description"

   "Submission data", "Those are the data associated with a submission such as the filled forms and selectors provided by the Whistleblower."
   "Submission files", "Those are the files associated with a submission that may require to be handled with special care due to per recipient’s encryption and optional metadata cleanup."
   "Configuration data", "Those are all the data for the configuration and customization of the platform."
   "Software files", "Those are all the files of the software required to work."
   "Notification data", "Data sent to notify recipients of a new report via email"

Below a matrix showing different security measures applied on data.

.. csv-table::
   :header: "Data", "Encryption", "Metadata cleanup", "Blacklisting", "Sanitization"

   "Questionnaire answers", "Encrypted on the database with per-user / per/submissions keys", "N/A", "Keyword blacklisting", "Antispam, Anti XSS"
   "Report attachments", "Encrypted on the filesystem with per-user / per/submissions keys", "Optional", "Extension blocking, Antivirus", "N/A"
   "Platform configuration", "Encrypted database with admin password", "N/A", "N/A", "N/A"
   Software files", "N/A", "N/A", "N/A", "N/A"
   "Email notifications", "Encrypted with PGP when recipients keys are available", "N/A", "Antispam to prevent flooding", "N/A"

Threats to Privacy and Anonymity
================================
In this section are highlighted several threats that require specific explanation.

Browser History and Cache
-------------------------
GlobaLeaks tries to avoid, by using properly crafted HTTP headers, to leak information into actor’s browser history and cache. This privacy feature cannot guarantee the user to be safe against a forensics analysis of their browser cache and/or history but is provided as additional safety measure.

Metadata
--------
Every file can contain metadata related to the author or the whistleblower. The cleanup of metadata of submitted files is a particular topic that attempts to protect an “unaware” whistleblower from leaking information in a document that may pose their anonymity at risk. In the context of GlobaLeaks no automatic metadata cleanup is implemented because metadata is considered fundamental in the evidence preservation. For that reason metadata cleanup is an optional feature at choice of Whistleblower and/or Recipient.

Environmental Factors
---------------------
GlobaLeaks does not protect against environmental factors related to one actors physical location and/or their social relationships. For example if users have a video bug installed in their house to monitor all their activity Globaleaks cannot protect them. As well if whistleblowers, supposed to be anonymous, tells their story to friends or coworkers, GlobaLeaks cannot protect them.

Incorrect Data Retention Policies
---------------------------------
GlobaLeaks implements by default a strict data retention policy of 90 days to enable users to operate on the report for a limited time necessary for the invertigations.
If the platform is configured to retain every report for a long time and Recipients do not delete manually the unnecessary reports, the value of the platform data for an attacker increases and so the risk.

Human Negligence
----------------
While we do provide the Administrator the ability to fine tune their security related configurations and continuously inform the actors about their security related context at every step of interactions, GlobaLeaks cannot protect against any major security threats coming from human negligence. For example a Whistleblower submitting data for which is clear to third party (carrying on ex-post possible investigation to identify him) that he is the only and unique owner of that data, cannot be protected by GlobaLeaks.

Data Stored Outside GlobaLeaks
------------------------------
GlobaLeaks does not provide any kind of security for data that are stored outside the GlobaLeaks system. 
The duty of protection for such kind of data is exclusively of the actor.

Advanced Traffic Analysis
-------------------------
An attacker monitoring HTTPS traffic with no ability to decrypt it, is able to identify the role of the intercepted users, because Whistleblower, Recipient and Administrator interfaces generate different network traffic patterns. GlobaLeaks does not provide protection against this threat. It’s suggested to use Tor pluggable transports or other methods providing additional set of protections against this kind of attack.
