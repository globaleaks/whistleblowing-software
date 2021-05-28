User Interface
==============
This section presents a summary of the user interface offered to admin users.

Any time you log in as administrator via the login page, the application takes you to your personal administrative homepage; This page includes documentation for GlobaLeaks clarifying software security, best practices and community support.

From this home page, you may access all the common user facilities already described in the general user documentation.

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

Site Settings
-------------
This section offers you all the main customization possibilities necessary for implementing a basic and functional whistleblowing site.

This section is further divided in:

   1. Main configuration

   2. Theme customization

   3. Files

   4. Languages

   5. Text customization

Main Configuration
..................
This section details configuring the logo and all the text of the main user interfaces.

.. image:: ../../images/admin/site_settings_main_configuration.png

Theme Customization
...................
This section details loading CSS and JavaScript files necessary to customize the interface.

.. image:: ../../images/admin/site_settings_theme_customization.png

Files
.....
This section details loading any file you need to present whistleblowers with via the platform (e.g. a policy in PDF), or files required by your CSS and JavaScript customization.

.. image:: ../../images/admin/site_settings_files.png

Languages
.........
In this section you can turn on all languages required by your project, and set the default language.

.. note::
   Thanks to a great voluneer community, under leadership of the `Localization Lab <https://www.localizationlab.org/>`_, the software is already available and continously made available in a lot of languages. This aspect of internationalization is crucial in many projects. If you are starting a project and find the required languages are not available, we strongly invite you to register on our `web translation platform <https://www.transifex.com/otf/globaleaks/>`_ to facilitate the translation. Thank you!

.. image:: ../../images/admin/site_settings_languages.png

Text Customization
..................
Here you can configure overrides for any of the texts on the platform and of their respective translations.

.. image:: ../../images/admin/site_settings_text_customization.png

Users
-----
This sections details creation and managing users.
A basic system set up by completing the initial platform wizard is configured with an administrator and a recipient.

Depending on your project needs, you can create users with different roles and manage their respective privileges here.

.. image:: ../../images/admin/users.png

User Roles
..........
You can create users that have the following roles:

   1. Administrators

   2. Recipients

Administrators
++++++++++++++
TODO

Recipients
++++++++++++++
TODO

Questionnaires
--------------
This section details creating and managing whistleblowing questionnaires.

By default the software implements a default questionnaire with a single step and the following three questions:

   One "Short description" question of type "Multi-line text input" lets whistleblowers provide a short summary of the fact reported;

   One "Full description" question of type "Multi-line text input" lets whistleblowers describe the facts reported in detail;

   One "Attachments" question of type "Attachment" lets users load one or more attachments.

A basic system set up using the platform wizard has this default questionnaire pre-associated to the default context.

Depending on your project needs, you could create specific questionnaire for each of your different reports' contexts.

.. image:: ../../images/admin/questionnaires.png

Depending on your project needs, you may evaluate defining some questions once as question templates and reuse them in multiple questionnaires.

.. image:: ../../images/admin/question_templates.png

Steps
.....
You can organise questionnaire in one or multiple steps.
The default questionnaire is presented as a single step that includes all the questions.

Questions Types
...............
The software lets you to create questions of the following types:

   1. Single-line text input

   2. Multi-line text input

   3. Selection box

   4. Multiple-choice input

   5. Checkbox

   6. Attachment

   7. Terms of service

   8. Date

   9. Date range

   10. Map

   11. Question group

General Question Properties
...........................
Each of the software question types make it possible to configure the following properties:

  Question: The text of the question

  Hint: A hint that will be shown via a popover.

  Description: A description text that will be shown below the question

  Required: Set this field if you want the question to be mandatory

  Preview: Set this field if you want the answers to this question to appear in the preview section of the list

Question Properties by Question Type
....................................
Single and Multi-Line Text Input
++++++++++++++++++++++++++++++++
TODO

Selection Box, Multiple Choice Input, Checkbox
++++++++++++++++++++++++++++++++++++++++++++++
TODO

Question Groups
...............
TODO

Conditional Questions
.....................
TODO

Contexts
--------
In this section you can create and manage whistleblowing contexts (channels).

A whistleblowing channel is typically defined by the following main characteristics

    Name: The name of the channel
    Image: An image to identify the channel
    Description: A description of the channel
    Recipients: The set of recipients that will receive reports sent to this channel
    Questionnaire: The questionnaire that will be proposed to whistleblowers selecting this channel
    Submission expiration: The data retention policy for the channel

A basic system set up by completing the initial platform wizard is configured with a single context called "Default", with an associated recipient, and the default questionnaire.

Depending on your project needs, here you could create additional contexts and configure their respective recipients and properties.

.. image:: ../../images/admin/contexts.png

Submissions Expiration
......................
The software lets you configure a data retention policy for each channel.
This is a fundamental property of the whistleblowing channel, making it possible to configure automatic secure deletion of reports after a certain period of time.
This setting should be configured in relation to the risk of the channel, in order to limit unnecessary exposure of the reports received therein.

By default a context is configured with a report expiration of 30 days.

Case Management
---------------
This section is intended to host all the main case management features offered by the software.
Currently it hosts the possibility of defining report statuses and sub-statuses intended to be used by recipients while working on the reports.

By default the system includes the following report statuses:

   1. New

   2. Open

   3. Closed

Within this section you can add additional statuses other than the "Open" and "Closed" state, and you can also define sub-statuses for the closed status (e.g. Archived / Spam)

.. image:: ../../images/admin/report_statuses.png

Notification Settings
---------------------
This is the section where are configured all the aspects related to the mail notifications sent by the software.

The section is further divided in:
   1. Main configuration

   2. Notification templates

Main configuration
..................
Here you will find the technical configuration details for SMTP.

.. note::
   By default GlobaLeaks comes with a working configuration based on systems offered by the GlobaLeaks developers to the community of users and testers; even though this configuration is designed with special care with regards to security and privacy, consider using an alternative setup for your production environment.

.. image:: ../../images/admin/notification_settings.png

Notification Templates
......................
In this section are configured the notification templates.

By default GlobaLeaks includes text and translations for each of the templates provided, to be fully functional and researched with particular care with respect to security and privacy.
Depending on your project needs, you may override the default text with your customized one.

.. image:: ../../images/admin/notification_templates.png

Network Settings
----------------
This section details configuring the network settings.

The section is further divided in:
   1. HTTPS

   2. Tor

   3. IP Access control

HTTPS
.....
Here you can configure all the aspects related to the access of the platform via the HTTPS protocol.

.. image:: ../../images/admin/https.png

In particular here are configured:

   1. The domain name used by your project

   2. The HTTPS key and certificates

To ease the deployment and maintenance, and reduce the costs of your project, consider using the software-included support for the Let's Encrypt HTTPS certificates.

Tor
...
Here you can configure all the aspects related to the access of the platform via the Tor Protocol.

.. image:: ../../images/admin/tor.png

IP Access Control
.................
Here you can configure IP-based access-control.

.. image:: ../../images/admin/access_control.png

Suggested configurations are:

   1. Prevent Whistleblowers from reporting within their respective workspace.

   2. Restrict Recipients access to their intranet.

URL Redirects
.............
Here you can configure URL Redirects.

.. image:: ../../images/admin/url_redirects.png

Advanced Settings
-----------------
TODO

.. image:: ../../images/admin/advanced_settings.png

.. image:: ../../images/admin/anomaly_thresholds.png

Audit Log
---------
TODO

.. image:: ../../images/admin/audit_log_stats.png

.. image:: ../../images/admin/audit_log_activities.png

.. image:: ../../images/admin/audit_log_users.png

.. image:: ../../images/admin/audit_log_reports.png

.. image:: ../../images/admin/audit_log_scheduled_jobs.png
