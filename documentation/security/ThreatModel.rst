============
Threat Model
============
GlobaLeaks is an free and open source whistleblowing framework that can be used in many different usage scenarios that may require very different approaches to obtain at the same time strong security and high usability. This two requirements are necessary to safely handle a whistleblowing procedure by protecting whistleblowers and at the same time achieve specific project goals. For this reasons considering the variety of different use cases and risks the software supports the possibility to be configured o respond to the specific threat model here detailed.

This document is intended to be used by organizations intending to implement a whistleblowing procedure based on Globaleaks and support the analysis and understanding of the threat model of the context of use and of the risks involved and guide users through the selection of the practices to be used within their own project.

Actors Matrix
=============
As a first step we define the actors, which are the users that interact with a GlobaLeaks platform.

.. csv-table::
   :header: "Actor", "Definition"

   "Whistleblower", "The user who submits an anonymous report through the GlobaLeaks platform. Whistleblowers are persons in a wide range of different threat models depending on the usage scenario and the nature of information being submitted."
   "Recipient", "The user (person or organization) receiving the anonymous report submitted by the Whistleblower. The recipients act reasonably in good faith, e.g. if any of them were to give their credentials or private information to the attacker, that would be unreasonable."
   "Administrator", "The user (person or organization) that is running the GlobaLeaks platform. Administrator may not represent the same entity running, promoting and managing the whistleblowing initiatives (e.g., hosted solutions, multiple stakeholders projects, etc). The Administrator has to be considered in all scenarios described as a trusted entity with reference to the data exchanged by actors. The Administrator in most scenarios won’t be a trusted entity with respect to the identity of actors."

It’s highly relevant to apply each of the security measures always in relationship to the actors using GlobaLeaks, while always considering the security and usability tradeoff.

Anonymity Matrix
================
The anonymity of different actors must be differentiated and classified depending on the context of use represented by the following definitions:

.. csv-table::
   :header: "Actor", "Definition"

   "Anonymous", "Actor's identity and their location cannot be disclosed."
   "Confidential", "The system is designed to remove or limit any recording of identifiable information that when registered is maintained encrypted and managed confidentially."

Different uses of GlobaLeaks must consider the requirements for different actors in the anonymity matrix. The Anonymity level is reported in the user interface, with the aim of making the user aware of it. The Administrator can configure the Anonymity level required for each actor.

Communication Security Matrix
=============================
The security of communication with respect to third party transmission monitoring may have different requirements depending on its context of use.

.. csv-table::
   :header: "Security level", "Description"
   "High security", "The communication is encrypted end-to-end with the GlobaLeaks platform and no third party is in a condition to eavesdrop the communication."
   "Medium security", "The communication is encrypted end-to-end with the GlobaLeaks platform. A third party able to manipulate HTTPS security (e.g., Govt re-issuing TLS cert) is in a condition to eavesdrop the communication. If HTTPS security is guaranteed, Monitoring  actor’s communication’s line or the GlobaLeaks platform communication’s line is not possible."
   "No security", "The communication is not encrypted at all. Monitoring the communication’s line of the actor or of the GlobaLeaks platform is possible."

The following matrix applies the previous definition related to different architectural implementations of GlobaLeaks software:

.. csv-table::
   :header: "Communication security matrix", "Tor", "HTTPS"
   :header: "Actor", "Definition"

   "Security Level", "High security", "Medium security"

Identity Disclosure Matrix
==========================
Independently of the anonymity matrix, various actors may decide to, or be required to disclose or not disclose their identity.

.. csv-table::
   :header: "Identity disclosure matrix", "Definition"
   :header: "Actor", "Definition"

   "Undisclosed", "The actor's identity is not disclosed and its disclosure is not likely."
   "Partially disclosed (pseudonym)", "The actor operates under a pseudonym while interacting with the platform."
   "Optionally disclosed", "The actor’s identity is by default not disclosed, but they are given the chance to disclose it on a voluntary basis (e.g., in some workflows an anonymous tip-off MAY receive a follow-up, while a formal report with identity disclosed MUST receive a follow-up)."  
   "Disclosed", "The actor decides to, or is required to, disclose their identity to other actors."

Identity disclosure is a highly relevant topic, because even in an Anonymous High security environment, identity disclosure may be an valuable option for specific whistleblowing initiative workflows.

If an actor starts dealing with an Anonymity set “Anonymous” and with an “Undisclosed Identity” they can always decide, at a later stage, to disclose their identity. The opposite is not possible.
This is one of the key considerations to provide actors protection around GlobaLeaks.

Voluntary identity disclosure may be required in certain whisteblowing procedures because, generally:

* A tip off MAY receive a follow-up and can be anonymous;
* Formal reports MUST receive a follow-up and in that case cannot be anonymous.

The “MAY” vs. “MUST” is with respect to the actions of recipients and is a fundamental element of the guarantee provided to whistleblowers in many initiatives (e.g., a corporate or institutional whistleblowing platform should not follow a MUST approach for Anonymous submission follow-up, considering such submissions just tip offs and not formal reports). 

Usage Scenarios Matrix
======================
In this section you will find examples that show how different anonymity levels of different actors can be mixed together depending on the context of use.

.. csv-table::
   :header: "Use case", "Description"

   "Media outlet", "A Media outlet, whose identity is disclosed, decides to start a Whistleblowing initiative. The outlet's recipients are disclosed to Whistleblowers, so that they can trust a specific journalist rather than the outlet itself. Full anonymity must be assured to whistleblowers and their identity cannot be disclosed in connection with anonymous submissions. The whistleblower MAY choose to willingly disclose their identity (e.g. when the journalist's source-protection record is trusted)."
   "Corporate compliance", "A Corporation needs to implement transparency, or anti-bribery law compliance, by promoting its initiatives to employees, consultants and providers. The recipients are partially disclosed because they are represented by different divisions of the “Internal Audit” business unit of the company. The Whistleblower is guaranteed full anonymity, but they can optionally disclose their identity (tip off vs formal report)."
   "Government tax whistleblowing", "A Government Authority (central or local) with its own public identity wants to promote Tax Whistleblowing with Rewards procedures for Whistleblowers (e.g. IRS). The recipients are not known because they are an internal division not exposing their names to the Whistleblower in advance. The Whistleblower MUST disclose their identity in order to be eligible for rewards."
   "Human Rights Activism Initiative", "A Human Rights Group starts a Whistleblowing initiative to spot human rights violations in a dangerous place. The organization requires anonymity to avoid retaliations and takedowns, and operates under a Pseudonym. The Recipients MUST not be disclosed to the Whistleblowers, but a Partial Disclosure by pseudonym can be acceptable in order to give proper trust to “Who the whistleblower is submitting to” . The Whistleblower MUST be guaranteed anonymity and their identity cannot be disclosed."
   "Citizen media initiative", "A Citizen media initiative with it’s own public identity wants to collect tips on a specific topic (political, environmental malpractice, corruption, etc) in a medium-low risk operational context. The recipients could be public or use Pseudonym in order to avoid complete exposure. The Whistleblower, if the topic is not life-threatening, can be allowed to submit also in a Confidential way to lower the entrance barrier."
   "Public Agency Iniziative", "A local public agency wants to setup a Street Hole Reporting service with it’s own public identity. The recipient can be disclosed to facilitate the CRM (Citizen relationship management) and Whistleblower identity protection is not required."

GlobaLeaks Security Matrix
==========================
Below we show how different usage scenarios can require different anonymity levels, communication security requirements and identity disclosures for different actors.

GlobaLeaks, through its user interface, will enable each actor with appropriate security awareness information, and will enforce specific requirements to specific actors by the application of clear configuration guidelines.

.. csv-table::
   :header: "Scenario", "Actor", "Anonymity level", "Identity disclosure", "Communication security"

   "Media outlet", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "No anonymity", "Disclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "Corporate compliance", "Whistleblower", "Anonymous", "Optionally disclosed", "High security"
    "", "Recipient", "No anonymity", "Partially disclosed", "Medium security"
    "", "Admin", "No anonymity", "Disclosed", "Medium security"
   Government tax whistleblowing", "Whistleblower", "No anonymity", "Disclosed", "Medium security"
   "", "Recipient", "No anonymity", "Undisclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "Human Rights Activism initiative", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "Anonymous", "Partially disclosed", "High security"
   "", "Admin", "Anonymous", "Partially disclosed", "High security"
   "Citizen media initiative", "Whistleblower", "Confidential", "Optionally disclosed", "Medium security"
   "", "Recipient", "Confidential", "Confidential", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "Public agency initiative", "Whistleblower", "No anonymity", "Optionally disclosed", "No security"
   "", "Recipient", "No anonymity", "Undisclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"

The previous schema gives only some examples of GlobaLeaks’s flexibility; but different anonymity, identity and security measures apply to other usage scenarios and actors.

Data Security Matrix
====================
This section highlights the data that is handled by GlobaLeaks and how different protection schemes are applied to GlobaLeaks handled data.

The following information types are the one involved within GlobaLeaks:

.. csv-table::
   :header: "Information type", "Description"

   "Questionnaire answers", "The data associated with a submission such as the filled forms and selectors provided by the Whistleblower."
   "Submission attachments", "The files associated with a submission."
   "Platform configuration", "The data for the configuration and customization of the platform."
   "Software files", "All the files that the software requires to work, including configuration defaults."
   "Email notifications", "Data sent to notify recipients of a new report via email"

Below a matrix showing different security measures applied on data.

.. csv-table::
   :header: "Information type", "Encryption", "Metadata cleanup", "Blacklisting", "Sanitization"

   "Questionnaire answers", "Encrypted on the database with per-user / per-submissions keys", "N/A", "Keyword blacklisting", "Antispam, Anti XSS"
   "Submission attachments", "Encrypted on the filesystem with per-user / per/submissions keys", "Optional", "Extension blocking, Antivirus", "N/A"
   "Email notifications", "Encrypted with PGP when recipients keys are available", "N/A", "Antispam to prevent flooding", "N/A"

Threats to Anonymity and Confidentiality
========================================
In this section we highlight several threats that require specific explanation.

Browser History and Cache
-------------------------
GlobaLeaks tries to avoid, by using properly crafted HTTP headers and other triks, leaking information into any actor’s browser history or cache. This privacy feature cannot guarantee the safety of the user against a forensics analysis of their browser cache and/or history, but it is provided as an additional safety measure.

Metadata
--------
Every file can contain metadata related to the author or the whistleblower. The cleanup of metadata of submitted files is a particular topic that attempts to protect an “unaware” whistleblower from leaking information in a document that may put their anonymity at risk. In the context of GlobaLeaks, by default no automatic metadata cleanup is implemented because metadata is considered fundamental in the evidence preservation. For that reason metadata cleanup is an optional operation that coulld be suggested to Whistleblowers or operated by Recipients when sharing the document with other persons. A valuable software resource for this aim is the `Metadata Anonymization Toolkit <https://0xacab.org/jvoisin/mat2`_

Malware and Trojans
-------------------
GlobaLeaks could not prevent an attacker to use the platform maliciously trying to target recipients users with malware and trojans in general. Considering this and in order to be less vulnerable to risks of data exfiltration perpretrated with trojans, Recipients should always implement proper operation security by possibly using a laptop dedicated to reports visualization and possibly open file attachments on computers disconnected from the network and other sensible information. Wherever possible they should use operation with specialized secure operation systems like `QubesOS <https://www.qubes-os.org/>`_ or `Tails <https://tails.boum.org/>`_ or and at least run an up-to-date Anti-Virus software.

Data Stored Outside the Platform
--------------------------------
GlobaLeaks does not provide any kind of security for data that is stored outside the GlobaLeaks system. Is responsibility of Recipients to protect the data they download from the platform on their personal computer or that they share with other persons with external usb drives. The operatin system used or the pen drive adoptet should offer encryption and guarantee that in case of device loss or stealing no one could access the data therein contained.

Environmental Factors
---------------------
GlobaLeaks does not protect against environmental factors related to actors' physical locations and/or their social relationships. For example if a user has a video bug installed in their house to monitor all their activity, GlobaLeaks cannot protect them. Likewise, if a whistleblower, who is supposed to be anonymous, tells their story to friends or coworkers, GlobaLeaks cannot protect them.

Incorrect Data Retention Policies
---------------------------------
GlobaLeaks implements by default a strict data retention policy of 90 days to enable users to operate on the report for a limited time necessary for the investigations. If the platform is configured to retain every report for a long time and Recipients do not manually delete the unnecessary reports, the value of the platform data for an attacker increases and so too does the risk.

Human Negligence
----------------
While we do provide the Administrator the ability to fine tune their security related configurations, and while we do continuously inform the actors about their security related context at every step of interactions, GlobaLeaks cannot protect against any major security threats coming from human negligence. For example, if a Whistleblower submits data that a third party (carrying on an ex-post facto investigation) can use to identify them as the unique owner or recent viewer of that data, then the Whistleblower cannot be protected by GlobaLeaks.

Advanced Traffic Analysis
-------------------------
An attacker monitoring HTTPS traffic, with no ability to decrypt it, can still identify the role of the intercepted users, because the Whistleblower, Recipient and Administrator interfaces generate different network traffic patterns. GlobaLeaks does not provide protection against this threat. We suggest using `Tor pluggable transports <https://2019.www.torproject.org/docs/pluggable-transports.html.en>`_ or other methods that provide additional protection against this kind of attack.
