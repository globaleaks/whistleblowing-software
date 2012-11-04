
# Scheduled operation in GLBackend

In this directory are implemented the asynchronous operation used in GLBackend. The operative
roles of those classes 

## Files

Those file are called with the \_sched.py suffix, to avoid same name mistakes (tip,
notification, delivery, statistics, would be used also in models, in modules and in handlers)

    delivery\_sched.py
        class APSDelivery
    notification\_sched.py
        class APSNotification
    statistics\_sched.py
        class APSStatistics
    tip\_sched.py
        class APSTip
    welcome\_sched.py
        class APSWelcome
    cleaning\_sched.py
        class APSCleaning

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
