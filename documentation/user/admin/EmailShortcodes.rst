==============
Email shortcuts
==============

What is email shortcodes?
-------------------------------------------
Under Notification Settings -> Notification templates you can find the emails which is sent out to recipients and admins.
There are shortcodes with dynamic links for the portal

Email shortcodes?
-------------------------------------------

``{RecipientName}`` = The name of the recipient <br>
``{Url}`` = URL of the exact whistleblowing (viewed by recipients) <br>
``{LoginUrl}`` = Login page of the portal <br>
``{AdminCredentials}`` = Admin password (only useable when a new GlobaLeaks Platform is made)<br>
``{RecipientCredentials}`` = Recipient password (only useable when a new GlobaLeaks Platform is made)<br>
``{DocumentationUrl}`` = The URL for user documentation of GlobaLeaks<br>
``{NodeName}`` = The name of the recipient or admin<br>
``{AccountRecoveryKeyInstructions}`` = Intruction of how to reset the password<br>
``{ActivityDump}`` = In event of unusual activity the activity will be sent in the email<br>
``{FreeMemory}`` = How much memory is free on the disk Globaleaks runs on<br>
``{TotalMemory}`` = How much total memory is on the disk Globaleaks runs on<br>
``{AnomalyDetailDisk}`` & ``{AnomalyDetailActivities}``  = A dump of abnormal activity in the ststen<br>
``{PGPKeyInfoList}`` = List over the PGP keys in the system<br>
``{NewEmailAddress}`` = This is for when a email is changed to a new one <br>
``{ExpiringSubmissionCount}`` = Number of whistleblowings which is about to expire <br>
``{EarliestExpirationDate}`` = The earliest date of expiration  <br>
``{ChangeLogUrl}`` = The changelog which is sent when a new update is available   <br>
``{UpdateGuideUrl}`` = How to update guide






Used when exporting whistleblows
-------------------------------------------
``{Author}`` = Auther of the messege<br>
``{EventTime}`` = Timestamp of the event <br>
``{Content}`` = Content of the messege or whistleblow <br>
``{Author}`` = Auther of the messege<br>
``{TipNum}`` = The ID of the whistleblow <br>
``{TipLabel}`` = The label which have been given to the whistleblow<br>
``{TipStatus}`` = The status of the whistleblow<br>
``{ContextName}`` = Context which the whistleblow was in<br>
``{QuestionnaireAnswers}`` = Answers to questionnaires<br>
``{Comments}`` = Comments to questionnaires<br>
``{Messages}`` = Messages in questionnaires<br>
``{ExpirationDate}`` = The day where the platform will be deleted or the TLS certificate expires  <br>


Only used on try.globaleaks.com
-------------------------------------------
``{Name}`` = Name of the registant<br>

