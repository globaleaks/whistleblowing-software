==============
Email shortcuts
==============

What is email shortcodes?
-------------------------------------------
Under Notification Settings -> Notification templates you can find the emails which is sent out to recipients and admins.
There are shortcodes with dynamic links for the portal

Email shortcodes?
-------------------------------------------

|``{RecipientName}`` = The name of the recipient 
|``{Url}`` = URL of the exact whistleblowing (viewed by recipients) 
|``{LoginUrl}`` = Login page of the portal 
|``{AdminCredentials}`` = Admin password (only useable when a new GlobaLeaks Platform is made)
``{RecipientCredentials}`` = Recipient password (only useable when a new GlobaLeaks Platform is made)
``{DocumentationUrl}`` = The URL for user documentation of GlobaLeaks
``{NodeName}`` = The name of the recipient or admin
``{AccountRecoveryKeyInstructions}`` = Intruction of how to reset the password
``{ActivityDump}`` = In event of unusual activity the activity will be sent in the email
``{FreeMemory}`` = How much memory is free on the disk Globaleaks runs on
``{TotalMemory}`` = How much total memory is on the disk Globaleaks runs on
``{AnomalyDetailDisk}`` & ``{AnomalyDetailActivities}``  = A dump of abnormal activity in the ststen
``{PGPKeyInfoList}`` = List over the PGP keys in the system
``{NewEmailAddress}`` = This is for when a email is changed to a new one 
``{ExpiringSubmissionCount}`` = Number of whistleblowings which is about to expire 
``{EarliestExpirationDate}`` = The earliest date of expiration  
``{ChangeLogUrl}`` = The changelog which is sent when a new update is available   
``{UpdateGuideUrl}`` = How to update guide






Used when exporting whistleblows
-------------------------------------------
``{Author}`` = Auther of the messege
``{EventTime}`` = Timestamp of the event 
``{Content}`` = Content of the messege or whistleblow 
``{Author}`` = Auther of the messege
``{TipNum}`` = The ID of the whistleblow 
``{TipLabel}`` = The label which have been given to the whistleblow
``{TipStatus}`` = The status of the whistleblow
``{ContextName}`` = Context which the whistleblow was in
``{QuestionnaireAnswers}`` = Answers to questionnaires
``{Comments}`` = Comments to questionnaires
``{Messages}`` = Messages in questionnaires
``{ExpirationDate}`` = The day where the platform will be deleted or the TLS certificate expires  


Only used on try.globaleaks.com
-------------------------------------------
``{Name}`` = Name of the registant

