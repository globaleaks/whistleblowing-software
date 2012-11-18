#!/bin/sh

SHOOTER="python shooter.py"

force_jobs() {
    # force the job
    $SHOOTER A6 GET oid delivery 
    if [ $? != 0 ]; then echo "\tError in A6 GET (force delivery job)" && exit; fi
    $SHOOTER A6 GET oid notification
}

if [ -n "$1" ]; then
    echo "If an option is present, is choosen as context_gus"
    context_gus=$1
else
    context_gus=`$SHOOTER U1 GET print-context_gus | head -1`
    if [ $? != 0 ]; then echo "\tError in U1 GET $context_gus" && exit; fi
    echo "context_gus $context_gus"
fi

submission_gus=`$SHOOTER U2 GET cid $context_gus print-submission_gus`
if [ $? != 0 ]; then echo "\tError in U2 GET $submission_gus" && exit; fi

$SHOOTER U3 POST sid $submission_gus
if [ $? != 0 ]; then echo "\tError in U3 POST" && exit; fi

$SHOOTER U4 POST sid $submission_gus 
if [ $? != 0 ]; then echo "\tError in U4 POST" && exit; fi

$SHOOTER A6 GET oid tip 
if [ $? != 0 ]; then echo "\tError in A6 GET (force tip job)" && exit; fi

force_jobs

# now we need to be the receiver with the tip, and vote pertinence.

tip_gus_list=`$SHOOTER A5 GET oid itip print-tip_gus | grep -v None`
if [ $? != 0 ]; then echo "\tError in A5 GET (list of itip)" && exit; fi
for tip_gus in $tip_gus_list; do
    $SHOOTER T1 POST tip $tip_gus variation vote
    if [ $? != 0 ]; then echo "\tError in T1 POST (expressing pertinence vote)" && exit; fi
    echo -n "."
done

force_jobs
echo "\nwant to see InternalTip ? $SHOOTER A5 GET oid itip verbose"
