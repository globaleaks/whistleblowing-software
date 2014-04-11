
# Scheduled operation in GLBackend

In this directory are implemented the asynchronous operation used in GLBackend. The operative
roles of those classes 

## Files

Those file are called with the \_sched.py suffix, to avoid same name mistakes (tip,
notification, delivery, statistics, would be used also in models, in modules and in handlers)

    delivery_sched.py
        class DeliverySchedule

 **delivery** prepare the receiver Folder to be downloaded or sent them in the remote way,
 specified by the delivery module.

    notification_sched.py
        class NotificationSchedule

 **notification** send the Tip authenticative string to the receiver, using the configured
 module.

    statistics_sched.py
        class StatisticsSchedule

 **statistics** every TOT minutues a new statistics row is created, where would be collected
 the event of the next timeframe. 

    tip_sched.py
        class TipSchedule

 **tip** create the ReceiverTip, this operation was part of the finalize operation executied
 in the Cyclone flow. Tip operation instead would be time consuming, and require to be managed
 in asynchronous way, to manage features.

    cleaning_sched.py
        class CleaningSchedule

 **cleaning** remove old Tip, unfinished sumibssion and elements that reach an expiring date.

    digest_sched.py
        class DigestSchedule

 **digest** manage the message queue for the mail subsistem, append the message present in a
 timeframe in the same mail, avoiding massive notification in case of huge Tip activities.

## Status tracking

Every running job is not stateful, and its state is not saved. The **trigger** of the
operation, instead is tracked inside the resource. in example:

**Submission** class has a marker inside (field 'mark'), and can have two values:

   incomplete
   finalized

and the asyncronous operation that conver the submission in receiver tip (whistleblower tip
is created runtime with the finalize operation) if is interrupted during the process, simply 
run another time the ReceiverTip creation)

**ReceiverTips** class has marker inside, about the notification status and the delivery
status. actually the notification marker planned are:

    not notified
    notified
    unable to be notified

delivery marks, describe the various status that can be in Folder:

    no data available
    not yet delivered
    delivery available 
    delivery performed 
    unable to be delivered

If notification or delivery is intrrupted during the process, need to be redone. When the
operation is complete, the marker is flipped with the appropriate stage.

"delivery available" mean that delivery would be performed by receivers will. like downloading
a file. also in that case, 'not yet delivered' is the marker before create a zip file (or the 
encrypted version for every receiver)

## Possible usage, extension, interactions
