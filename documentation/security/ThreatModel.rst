============
Threat Model
============
GlobaLeaks is an free and open source whistleblowing software that can be used in many different usage scenarios that may require very different approaches to obtain at the same time strong security and high usability. This two requirements are necessary to safely handle a whistleblowing procedure by protecting whistleblowers and at the same time achieve specific project goals. For this reasons considering the variety of different use cases and risks the software supports the possibility to be configured o respond to the specific threat model here detailed.

This document is intended to be used by organizations that want to implement a whistleblowing procedure based on Globaleaks and support the analysis and comprehension of the specific threat model of their context of use and of the risks involved and guide users through the selection of the best practices to be used within their own project.

Users Matrix
============
As a first step we define the type of users that can interact with a GlobaLeaks platform.

.. csv-table::
   :header: "User", "Definition"

   "Whistleblower", "The user who submits an anonymous report through the platform. Whistleblowers are persons operating in a wide range of different threat models depending on the usage scenario and the nature of information being submitted."
   "Recipient", "The user receiving anonymous reports submitted by Whistleblowers and responsible for their analysis. Recipients act reasonably in good faith and have to be considered in all scenarios described as trusted party with reference to the protection of Whistleblowers' and the confidentiality of the information by them communicated."
   "Administrator", "The users supporting the setup, the management and monitoring the security of the platform. Administrator may not represent the same entity running, promoting and managing the whistleblowing initiatives (e.g., hosted solutions, multiple stakeholders projects, etc). The Administrator has to be considered in all scenarios described as a trusted entity. They do not have direct access to reports and they are responsible for advising Recipients on the best practices to be adopted in their work."

It's highly relevant to apply each of the security measures always in relationship to the users using the platorm, trying to identify an adequate security and usability tradeoff.

Anonymity Matrix
================
The anonymity of different users must be differentiated and classified depending on the context of use represented by the following definitions:

.. csv-table::
   :header: "User", "Definition"

   "Anonymous", "The user has accessed the platform via the Tor Browser and following the best practices for protecting their identity reducing to the maximum the possibility that a system involved in the operation has tracked their activities and their own IP address. The user has not provided any information about their own identity to Recipients."
   "Confidential", "The user has used the platform by using a common browser. In this case, third parties could have logged their IP address during their operations but the platform has protected the content of their communication. The user may have possibly opted for disclosing confidentially their own identity to Recipients."

The platform always reports to users their current anonymity state and inform them about the best practices for accessing anonymously via the Tor Browser. Depending on the use case Administrators could possibly enforce the requirement that Whistleblowers could file reports only by using the Tor Browser.

Communication Security Matrix
=============================
The security of communication with respect to third party transmission monitoring may have different requirements depending on its context of use.

.. csv-table::
   :header: "Security level", "Description"
   "High security", "Tor is used and the communication is encrypted end-to-end with the GlobaLeaks platform and no third party is in a condition to eavesdrop the communication."
   "Medium security", "HTTPS is used and the communication is encrypted end-to-end with the GlobaLeaks platform. A third party able to manipulate HTTPS security (e.g., Govt re-issuing TLS cert) is in a condition to eavesdrop the communication. If HTTPS security is guaranteed, Monitoring  user's communication's line or the GlobaLeaks platform communication's line is not possible."

==========================
Independently of the anonymity matrix, various users may decide to, or be required to disclose or not disclose their identity.

.. csv-table::
   :header: "Identity disclosure matrix", "Definition"
   :header: "User", "Definition"

   "Undisclosed", "The user's identity is not disclosed and its disclosure is not likely."
   "Optionally disclosed", "The user's identity is by default not disclosed, but they are given the chance to disclose it on a voluntary basis (e.g., in some workflows an anonymous tip-off MAY receive a follow-up, while a formal report with identity disclosed MUST receive a follow-up)."
   "Disclosed", "The user decides to, or is required to, disclose their identity to other users."

Identity disclosure is a highly relevant topic, because even in an Anonymous High security environment, identity disclosure may be an valuable option for specific whistleblowing initiative workflows.

If a user starts dealing with an Anonymity set “Anonymous” and with an “Undisclosed Identity” they can always decide, at a later stage, to disclose their identity. The opposite is not possible.
This is one of the key considerations to provide users protection around GlobaLeaks.

Voluntary identity disclosure may be required in certain whisteblowing procedures because, generally:

* A tip off MAY receive a follow-up and can be anonymous;
* Formal reports MUST receive a follow-up and in that case cannot be anonymous.

The “MAY” vs. “MUST” is with respect to the actions of recipients and is a fundamental element of the guarantee provided to whistleblowers in many initiatives (e.g., a corporate or institutional whistleblowing platform should not follow a MUST approach for Anonymous submission follow-up, considering such submissions just tip offs and not formal reports). 

Usage Scenarios Matrix
======================
In this section you will find examples that show how different anonymity levels of different users can be mixed together depending on the context of use.

.. csv-table::
   :header: "Use case", "Description"

   "Media outlet", "A Media outlet, whose identity is disclosed, decides to start a Whistleblowing initiative. The outlet's recipients are disclosed to Whistleblowers, so that they can trust a specific journalist rather than the outlet itself. Full anonymity must be assured to whistleblowers and their identity cannot be disclosed in connection with anonymous submissions. The whistleblower MAY choose to willingly disclose their identity (e.g. when the journalist's source-protection record is trusted)."
   "Corporate compliance", "A Corporation needs to implement transparency, or anti-bribery law compliance, by promoting its initiatives to employees, consultants and providers. The recipients are part of a division of the company (e.g. Internal Audit office). The Whistleblower is guaranteed full anonymity, but they can optionally disclose their identity."
   "Human Rights Activism Initiative", "A Human Rights Group starts a Whistleblowing initiative to spot human rights violations in a dangerous place. The organization requires anonymity to avoid retaliations and takedowns, and operates under a pseudonym. The Recipients MUST not be disclosed to the Whistleblowers, but a Partial Disclosure by pseudonym can be acceptable in order to give proper trust to “Who the whistleblower is submitting to” . The Whistleblower MUST be guaranteed anonymity and their identity cannot be disclosed."
   "Citizen media initiative", "A Citizen media initiative with it's own public identity wants to collect reports on a specific topic (political, environmental malpractice, corruption, etc) in a medium-low risk operational context. The recipients could be public or use Pseudonym in order to avoid complete exposure. The Whistleblower, if the topic is not life-threatening, can be allowed to submit also in a Confidential way to lower the entrance barrier."

Below we show how different usage scenarios can require different anonymity levels, communication security requirements and identity disclosures for different users.

GlobaLeaks, through its user interface, will enable each user with appropriate security awareness information, and will enforce specific requirements to specific users by the application of clear configuration guidelines.

.. csv-table::
   :header: "Scenario", "User", "Anonymity level", "Identity disclosure", "Communication security"

   "Media outlet", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "No anonymity", "Disclosed", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "Corporate compliance", "Whistleblower", "Anonymous", "Optionally disclosed", "High security"
    "", "Recipient", "No anonymity", "Partially disclosed", "Medium security"
    "", "Admin", "No anonymity", "Disclosed", "Medium security"
   "Human Rights Activism initiative", "Whistleblower", "Anonymous", "Undisclosed", "High security"
   "", "Recipient", "Anonymous", "Partially disclosed", "High security"
   "", "Admin", "Anonymous", "Partially disclosed", "High security"
   "Citizen media initiative", "Whistleblower", "Confidential", "Optionally disclosed", "Medium security"
   "", "Recipient", "Confidential", "Confidential", "Medium security"
   "", "Admin", "No anonymity", "Disclosed", "Medium security"

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
   :header: "Information type", "Encryption", "Filters", "Sanitization"

   "Questionnaire answers", "Encrypted on the database with per-user / per-submissions keys", "Keyword filters", "Antispam, Anti XSS"
   "Submission attachments", "Encrypted on the filesystem with per-user / per/submissions keys", "Extension blocking, Antivirus", "N/A"
   "Email notifications", "Encrypted with PGP when recipients keys are available", "Antispam to prevent flooding", "N/A"

Threats to Anonymity and Confidentiality
========================================
In this section we highlight several threats that require specific explanation.

Browser History and Cache
-------------------------
GlobaLeaks tries to avoid, by using properly crafted HTTP headers and other techniques, leaking information into any user's browser history or cache. This privacy feature cannot guarantee the safety of the user against a forensics analysis of their browser cache and/or history, but it is provided as an additional safety measure.

Metadata
--------
Every file can contain metadata related to the author or the whistleblower. The cleanup of metadata of submitted files is a particular topic that attempts to protect an “unaware” whistleblower from including information in a document that may put their anonymity at risk. In the context of GlobaLeaks, by default no automatic metadata cleanup is implemented because metadata is considered fundamental part of the original evidence that shall be preserved and not invalidated. For this reason metadata cleanup is an optional operation that could be suggested to Whistleblowers or operated by Recipients when sharing the document with other persons. When sharing files to external third parties Recipients are invited to print the document and provide a hard copy. This process is helpful to ensure that recipients only share what they see without risking to share sensitive information contained in the metadata of the files of which they may not be aware of. To get to know more about metadata and the best practices on redacting metadata from digital files we recommend reading the article `Everything you wanted to know about media metadata, but were afraid to ask <https://freedom.press/training/everything-you-wanted-know-about-media-metadata-were-afraid-ask/>`_ by Harlo Holmes. A valuable tool supporting these advanced procedures is the `Metadata Anonymization Toolkit <https://0xacab.org/jvoisin/mat2>`_

Malware and Trojans
-------------------
GlobaLeaks could not prevent an attacker to use the platform maliciously trying to target recipients users with malware and trojans in general. Considering this and in order to be less vulnerable to risks of data exfiltration perpretrated with trojans, Recipients should always implement proper operation security by possibly using a laptop dedicated to reports visualization and open file attachments on computers disconnected from the network and other sensible information. Wherever possible in their operation they should adopt specialized secure operation systems like `QubesOS <https://www.qubes-os.org/>`_ or `Tails <https://tails.boum.org/>`_ or and at least run an up-to-date Anti-Virus software.

Network and Reverse Proxies
---------------------------
GlobaLeaks is intended to be used by end users with a direct Tor or TLS connection from the browser of the user to the application backend. Any use of Network and Reverse Proxies in front of the application is discouraged; those appliances could significatively interfere with the application and lower its security vanishing any confidentility and anonimity measure implemented within GlobaLeaks.

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
While we do provide the Administrator the ability to fine tune their security related configurations, and while we do continuously inform the users about their security related context at every step of interactions, GlobaLeaks cannot protect against any major security threats coming from human negligence. For example, if a Whistleblower submits data that a third party (carrying on an ex-post facto investigation) can use to identify them as the unique owner or recent viewer of that data, then the Whistleblower cannot be protected by GlobaLeaks.

Advanced Traffic Analysis
-------------------------
An attacker monitoring HTTPS traffic, with no ability to decrypt it, can still identify the role of the intercepted users, because the Whistleblower, Recipient and Administrator interfaces generate different network traffic patterns. GlobaLeaks does not provide protection against this threat. We suggest using `Tor pluggable transports <https://2019.www.torproject.org/docs/pluggable-transports.html.en>`_ or other methods that provide additional protection against this kind of attack.
