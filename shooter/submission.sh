#!/bin/sh

SHOOTER="python shooter.py"

#
# This script wrap the shooter.py script. do not include any of the globaleaks files
#

if [ -n "$1" ]; then
    echo "If an option is present, is choosen as context_gus"
    context_gus=$1
else
    context_gus=`$SHOOTER U1 GET print-context_gus`
    if [ $? != 0 ]; then echo "\tError in U1 GET" && exit; fi
    echo "context_gus $context_gus"
fi

# the first command line optionally used, is 
#
# python shooter.py U1 GET
# and is equivalent to:
# python shooter.py node GET
# 
# the option print-context_gus mean that the first entry of the returned dict
# with the key context_gus,is printed in stdout.
#
# using 'verbose' you can see all the sent and received dict.


# A5 is an administrative interface that permit the dump of a table. internaltip in this case,
# is used to count the amount of internaltips present in the system.
beforecount=`$SHOOTER A5 GET oid itip print-elements`
if [ $? != 0 ]; then echo "\tError in A5 GET" && exit; fi

# open a new submission using U2, and specify which context is used when opened, return
# submission_gus, the globaleaks unique string usable as token
submission_gus=`$SHOOTER U2 GET cid $context_gus print-submission_gus`
if [ $? != 0 ]; then echo "\tError in U2 GET" && exit; fi
echo "submission_gus $submission_gus"

# get the submission status using the submnission token
$SHOOTER U3 GET sid $submission_gus
if [ $? != 0 ]; then echo "\tError in U3 GET" && exit; fi

# post-update the submission status, passing the fields and optionally others stuff
$SHOOTER U3 POST sid $submission_gus
if [ $? != 0 ]; then echo "\tError in U3 POST" && exit; fi

# get the receipt, using the verbose option it's printed.
$SHOOTER U4 POST sid $submission_gus verbose
if [ $? != 0 ]; then echo "\tError in U4 POST" && exit; fi

# A6 is an administrative interface that force the execution of the Tip, otherwise scheduled,
# job. -- this generate the ReceiverTip(s)
$SHOOTER A6 GET oid tip 
if [ $? != 0 ]; then echo "\tError in A6 GET (force tip job)" && exit; fi

# Get the number of internaltip, the forced job has cause the creation of the receivers tip
# here is checked in in backend side everything is going fine. the number of internaltip
# is recorded and compared with the previously collected number.
aftercount=`$SHOOTER A5 GET oid itip print-elements`
if [ $? != 0 ]; then echo "\tError in A5 GET" && exit; fi

if [ $((beforecount + 1)) != $aftercount ]; then
    echo "serious error in tip generation :("
else
    echo "correct InternalTip generation..."
fi

echo "forcing delivery job"
# Force ReceiverTip delivery and notification
$SHOOTER A6 GET oid delivery 
if [ $? != 0 ]; then echo "\tError in A6 GET (force delivery job)" && exit; fi
echo "forcing notification job"
$SHOOTER A6 GET oid notification
if [ $? != 0 ]; then echo "\tError in A6 GET (force notification job)" && exit; fi
