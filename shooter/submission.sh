#!/bin/sh

SHOOTER="python shooter.py"

if [ -n "$1" ]; then
    echo "If an option is present, is choosen as context_gus"
    context_gus=$1
else
    context_gus=`$SHOOTER U1 GET print-context_gus`
    if [ $? != 0 ]; then echo "\tError in U1 GET" && exit; fi
    echo "context_gus $context_gus"
fi


beforecount=`$SHOOTER A5 GET oid itip print-elements`
if [ $? != 0 ]; then echo "\tError in A5 GET" && exit; fi

submission_gus=`$SHOOTER U2 GET cid $context_gus print-submission_gus`
if [ $? != 0 ]; then echo "\tError in U2 GET" && exit; fi
echo "submission_gus $submission_gus"

$SHOOTER U3 GET sid $submission_gus
if [ $? != 0 ]; then echo "\tError in U3 GET" && exit; fi

$SHOOTER U3 POST sid $submission_gus
if [ $? != 0 ]; then echo "\tError in U3 POST" && exit; fi

$SHOOTER U4 POST sid $submission_gus verbose
if [ $? != 0 ]; then echo "\tError in U4 POST" && exit; fi

$SHOOTER A6 GET oid tip 
if [ $? != 0 ]; then echo "\tError in A6 GET (force tip job)" && exit; fi

aftercount=`$SHOOTER A5 GET oid itip print-elements`
if [ $? != 0 ]; then echo "\tError in A5 GET" && exit; fi

if [ $((beforecount + 1)) != $aftercount ]; then
    echo "serious error in tip generation :("
fi
