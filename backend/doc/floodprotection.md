# Flood Protection

GlobaLeaks is an application with various features prone to be DoSsed by attackers/spammers. 

  * **submission** is the procedure that permits to an anonymous user (hopefully, a whistleblower) to create an entry in the database, and trigger some notification and other CPU intensive operation like cryptography with public key for the recipients. 
  * **comment** is a text added by an anonymous user (the potential whistleblower that has performed the submission), authenticated in a previously created submission.
  * **file upload** is the operation, potentially Disk exhausting, performed by an anonymous user. this may happen during the submission or the in subsequent comment phases.

The basic measure to keep accounting, in order to avoid a node exhausted in resources, are:

  * submission number: every 30 seconds, if they overcome the number 2, is increased an anomaly counter (for example: from 0 to 1)
  * disk space: every 30 seconds is checked the amount of free space. When the free space start to be short, the anomaly tracker is increased.


## Token deploy roadmap

  * **upload a file** and **perform a submission** (and others, in the future) are operation CPU/Disk intensive, and left them available without any limits to an anonymous users, can expose GlobaLeaks software to flood and resources exhaustion.
  * Every user is pissed off if has to complete captchas, wait, etc. Every anti flood technology can be fooled in some way. We've defined 8 different enhancements along all the chain, that helps admin in deal with applicative DoS. They are: anomaly detection, alerting, slow down the requests. They will be triggered depending on the amount of stress present in the box. The limit of the anonymous network, is that you cannot recognize an IP address that is performing many connections and throttling it only.
  * The solution identified  consists in reducing as much as possible the CPU/Disk operation by an interaction with an anonymous user (don't apply to receiver activities, they are considered trusted).
  * Once reduced, via statistics and anomaly detection (they will be the next merged branch) is estimated a threshold on the alert. This replace the old anomaly detection system.
  * In the meantime, the hashcash, graphical captcha and human captcha are implemented. I'm thinking to try also a combination of two, having ['1', '+','2'] that can be image or text, supporting different numeric systems. 
  * The submission and file upload handlers are updated using the captcha, and submission became an atomic operation.
  * The **stress indicator** are two:
    * Number of activities happened in the latest minute (or other time unit, checked periodically)
    * Resources availability on the system (fixed threshold, for example, if a node has a file limit of 30 megabyte, when 300 Mb are available or 150 Mb are available, two separate level of alarm are triggered.)

To accomplish a CPU/Disk Intensive Operation (CDIO) a token is needed, and a token is usable only if the circumstances permit that.


## Threshold level

  * based on the value configured by Node admin 'max file size', we can know how many file upload can be supported. When 10 file are permitted, the Alarm level is increased to 1, when 5 file can be accepted, the level is raised to 2.
  * submission are set at 2 and comment too. These value at the moment are implemented in anomaly.py file

**when a threshold level is raised**, from 0 to 1 or 1 to 2, happens that:

  * in order to come back is needed a certain amount of time, the node will remain in "stress protection" for a certain amount of time (10 time the anomaly schedule, 300 seconds right now)
  * the admin is noticed about.
  * every Token requested include an enhancement on the authentication operation (captchas, hashcash, authenticate that the person is an human)

### Additional issue implications

  * statistics and anomaly detection depends on the activity amount, they are accounted in a dedicated queue.
  * realtime reporting: is possible dump the current queue of activity and report realtime to the admin, every time a GET is performed
  * mail reporting when alarm level is reached

### Token format

    token_id: a string composed by 42 alphanumeric data
    creation_date: the time which the token has been created (datetime format)
    start_validity: the time since the token can be used (datetime format)
    end_validity: the last second which the token can be used (datetime format)
    type: comment/submission/upload, specify which kind of operation is permitted with the token
    usages: an integer, specify how many times the token can be used. for comment and submission is always 1, but our client support multiple file upload, therefore the usage for this reason can be higher (10)
    h_captcha: human captcha, contain a question like "2+2" and is expected that answer in the token usage
    hashcash: a time consuming problem 
    g_captcha: a base64 image that contain a string, need to be resolved 


The token is always used as part of the URL requested. the problem resolution (captcha, hashcash) are part of the URL too. there is not a separated validation of the token. *atomicity, root of all goods*.

# Current status

  * captcha research in progress about language, localisation.
  * unitTested the token base system (unittest and handlers)
  * captcha validation using human captcha
  * still missing anything about hashcash
  * completed backend support for statistics, anomalies and activities (unitTest, handlers, TODO brainstorming on database)
  * research in progress for client timeline visualization, between timeline.js and d3.js
  * admin notification mail implemented, missing client side settings and mail templates.
  * Cache of public API merged in devel.


# That's all.
# That's all.


### minor notes:

## Admin notification

An admin has to be updated via email, (PGP encryption and Tor support by default, security can be disabled) whenever the node is under stress. 


### multiple file upload and space

The number of files that can be uploaded can vary on the alarm level threshold.


### The (active) anti flood subsystems

  * delay between access and submission: https://github.com/globaleaks/GlobaLeaks/issues/800
  * HashCash https://github.com/globaleaks/GlobaLeaks/issues/799
  * Human Captcha: https://github.com/globaleaks/GlobaLeaks/issues/795
  * Graphical Captcha https://github.com/globaleaks/GlobaLeaks/issues/198

### The (passive) anti flood subsystems:

  * caching of public API https://github.com/globaleaks/GlobaLeaks/issues/801
  * alert and logging (putting some attention to the size of the report) https://github.com/globaleaks/GlobaLeaks/issues/802
 
### Not submission related issues:

  * Notification limit https://github.com/globaleaks/GlobaLeaks/issues/798


