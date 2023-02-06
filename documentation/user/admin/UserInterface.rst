User Interface
==============
This section offers you a summary of the user interface offered to Admin users.

Anytime you log in as administrator via the Login page the application takes you to your personal administrative Homepage; This page includes some documentation about GlobaLeaks that is intended to clarify you all the up-to-date documentation in matter of software security, best practices and community support.

From this Home page you may access all the common user facilities already described in the general User Documentation.

.. image:: ../../images/admin/home.png

A menu on the right offers you links to the different administrative sections:

   1. Site settings

   2. Users

   3. Questionnaires

   4. Contexts

   5. Case management

   6. Notification settings

   7. Network settings

   8. Advanced settings

   9. System overview

Settings
--------
This is the section that offers you all the main customization possibilities necessary for implementing a basic and functional whistleblowing site.

This section is furtherly divided in:

   1. Settings

   2. Theme customization

   3. Languages

   4. Text customization

   5. Advanced settings

Settings
........
In this section is configurable the logo and all the texts of the main user interfaces.

.. image:: ../../images/admin/site_settings_main_configuration.png

Theme Customization
...................
In this section could be loaded CSS and Javascript files necessary to customize the interface.

.. image:: ../../images/admin/site_settings_theme_customization.png

Languages
.........
In this section you could enable all the languages required by your project and configure the default language.

.. note::
   Thanks to the `Localization Lab <https://www.localizationlab.org/>`_ and our great volunteer community, the software is already available and continuously made available in a lot of languages. This aspect of internationalization is crucial in many projects. In case you are starting a project and the required languages are not available we strongly invite you to register on our `web translation platform <https://www.transifex.com/otf/globaleaks/>`_ offered by `Transifex <https://www.transifex.com/otf/globaleaks/>`_ and support yourself the translation. Internationalization and Localization is in fact are crucial for the success of a whistleblowing project. Thank you!

.. image:: ../../images/admin/site_settings_languages.png

Text Customization
..................
Here could be configured overrides for any of the texts of the platform and of their translation.

.. image:: ../../images/admin/site_settings_text_customization.png

Advanced Settings
-----------------
In this section could be configured a set of advanced settings.

.. image:: ../../images/admin/advanced_settings.png

Users
-----
This sections is where users could be created and managed.
The system with the basic configuration completed with the initial Platform wizard is configured with an Administrator and a Recipient.

Depending on your project needs here you could create users with different roles and manage their respective privileges.

.. image:: ../../images/admin/users.png

User Roles
..........
The software offers the possibility to create users with the following roles:

   1. Administrators

   2. Recipients

Questionnaires
--------------
This section is where whistleblowing questionnaires could be created and managed.

By default the software implements a Default Questionnaire with a single Step and the following three questions:

   One question "Short description" of type "Multi-line text input" enabling whistleblower to provide a short summary of the fact reported;

   One question "Full description" of type "Multi-line text input" enabling whistleblowers to describe the fact reported in detail;

   One question "Attachments" of type "Attachment" enabling users to load one or more attachments.

The system with its basic configuration completed with the initial Platform wizard is also already configured with this Default Questionnaire pre-associated to the Default Context.

Depending on your project needs you could create specific questionnaire for each of your different reports' contexts.

.. image:: ../../images/admin/questionnaires.png

Depending on your project needs you may evaluate defining some questions once as Question Templates and reuse the same question in multiple questionnaires.

.. image:: ../../images/admin/question_templates.png

Steps
.....
The software enables to organize questionnaire in one or multiple steps.
For example the default questionnaire is organized with a single step including all the questions.

Questions Types
...............
The software enables you to create questions of the following types:

   1. Single-line text input

   2. Multi-line text input

   3. Selection box

   4. Multiple choice input

   5. Checkbox

   6. Attachment

   7. Terms of service

   8. Date

   9. Date range

   10. Question group

Common Question Properties
...........................
Each of the software question types make it possible to configure the following properties:

  Question: The text of the question

  Hint: A hint that will be shown via an popover an a question mark near the question.

  Description: A description text that will be shown below the question

  Required: Set this field if you want this question to be mandatory

  Preview: Set this field if you want the answers to this question to appear in the preview section of the  list 

Contexts
--------
This section is where whistleblowing contexts (channels) could be created and managed.

A whistleblowing channel is typically defined by the following main characteristics

    Name: the name of the channel
    Image: an image to identify the channel
    Description: a description of the channel
    Recipients: the set of recipients that will receive reports sent to this channel
    Questionnaire: the questionnaire that will be proposed to whistleblowers selecting this channel
    Submission expiration: the data retention policy for the channel

The system with the basic configuration completed with the initial platform wizard is configured with a single Context called Default, on which is associated a recipient and the default questionnaire.

Depending on your project needs here you could create additional Contexts and configure their respective recipients and properties.

.. image:: ../../images/admin/contexts.png

Submissions Expiration
......................
The software enables to configure a data retention policy for each channel.
This is a fundamental property of the whistleblowing channel that makes it possible to configure automatic secure deletion of reports after a certain period of time.
This setting should be configured in relation to the risk of the channel in order to limit unneeded exposure of the reports received therein.

By default a context is configured with a report expiration of 30 days.

Case Management
---------------
This section is intended to host all the main case management feature that will be offered by the software.
Currently it hosts the possibility to define reports statuses and sub-statuses intended to be used by Recipients while working on the reports.

By default the system includes the following report statuses:

   1. New

   2. Open

   3. Closed

Within this section you may add additional Statuses between the State Open and Closed and you can furtherly define Sub-statuses for the Closed status (e.g. Archived / Spam)

.. image:: ../../images/admin/report_statuses.png

Notification Settings
---------------------
This is the section where are configured all the aspects related to the mail notifications sent by the software.

The section is furtherly divided in:
   1. Main configuration

   2. Notification templates

Main configuration
..................
Here are configured the technical details about SMTP.

.. note::
   By default GlobaLeaks comes with a working configuration that is based on systems offered by the GlobaLeaks developers to the community of users and testers; even though this configuration is designed by their owners with special care in relation to security and privacy you are invited to consider using alternative systems for your production environment.

.. image:: ../../images/admin/notification_settings.png

Notification Templates
......................
In this section are configured the notification templates.

By default globaleaks includes text and translations for each of the templates that are provided to be fully functional and studied with particular care in relation to security and privacy.
Depending on your project needs you may override the default text with your customized texts.

.. image:: ../../images/admin/notification_templates.png

Network Settings
----------------
In this section are configured the network settings.

The section is furtherly divided in:
   1. HTTPS

   2. Tor

   3. IP Access control

   4. URL Redirects

HTTPS
.....
Here you can configure all the aspects related to the access of the platform via the HTTPS Protocol.

.. image:: ../../images/admin/https.png

In particular here are configured:

   1. The domain name used by your project

   2. The HTTPS key and certificates

To ease the deployment and the maintenance and reduce the costs of your project, consider using the software includes support for the Let’s Encrypt HTTPS certificates.

Tor
...
Here you can configure all the aspects related to the access of the platform via the Tor Protocol.

.. image:: ../../images/admin/tor.png

IP Access Control
.................
Here you can configure IP based Access Control.

.. image:: ../../images/admin/access_control.png

Suggested configurations are:

   1. Prevent Whistleblowers to report from within their respective work space.

   2. Restrict Recipients access to their intranet.

URL Redirects
.............
Here you can configure URL Redirects.

.. image:: ../../images/admin/url_redirects.png

Audit Log
---------
.. image:: ../../images/admin/audit_log.png

.. image:: ../../images/admin/audit_log_users.png

.. image:: ../../images/admin/audit_log_reports.png

.. image:: ../../images/admin/audit_log_scheduled_jobs.png

