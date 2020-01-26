==========
Encryption
==========
By default GlobaLeaks implements encryption for each submission protecting answers to the questionnaire, comments, attachments and involved metadata.
The keys involved in the encryption are per-user and per-submission and only users to which the data was destinated could access the data.
Keys are generated for each user at the first login and the keys are kept securely encrypted with a secret derived; This mechanism guarantees that only the user could access the data.
Please note that user would forget the password the data won’t be accessible anymore. In order to know about the features involved in account recovery and key escrow see the two specific sections on the topic.

Account recovery
----------------
To protect from possible password loss and corresponding data loss, users are entitled to download or print a personal recovery key and they could make this anytime via their profile section.
It is higly recommended to include this manual procedure in any user documentation requiring users to perform this operation before actually starting using the system.

Key escrow
----------
A key escrow mechanism is implemented by default and enables the admin user to restore user account on behalf of users in case of data loss.
This feature is automatically enabled on the first admin user created by the system and depending on the threat model and the organizational aspects of the projects this user is entitled to disable the feature or to enable it for other admin users.
