#!/bin/sh

SHOOTER="python shooter.py"

context_id=`$SHOOTER U1 GET sid print-id`
if [ $? != 0 ]; then echo "\tError in U1 GET" && exit; fi
echo "context_id $context_id"

submission_id=`$SHOOTER U2 GET print-submission_id`
if [ $? != 0 ]; then echo "\tError in U2 GET" && exit; fi
echo "submission_id $submission_id"

$SHOOTER U3 GET sid $submission_id
if [ $? != 0 ]; then echo "\tError in U3 GET" && exit; fi

$SHOOTER U3 POST sid $submission_id cid $context_id
if [ $? != 0 ]; then echo "\tError in U3 POST" && exit; fi

$SHOOTER U4 POST sid $submission_id verbose
if [ $? != 0 ]; then echo "\tError in U4 POST" && exit; fi
