#!/bin/sh

SHOOTER="./shooter.py"

#
# This script wrap the shooter.py script. do not include any of the globaleaks files


# disable scheduled operations
$SHOOTER AB DELETE oid alljobs

context_gus=`./shooter.py U6 GET verbose | sed -es/.*context_gus....//g | cut -b -22 | grep c_`

beforecount=`$SHOOTER AA GET oid itip print-elements`
echo "Internaltip numbers $beforecount"

submission_gus=`$SHOOTER U2 POST cid $context_gus print-submission_gus`
echo "submission token: $submission_gus"

receipt=`$SHOOTER U3 PUT cid $context_gus sid $submission_gus print-receipt`
echo "receipt $receipt"

beforecount=`$SHOOTER AA GET oid itip print-elements`
echo "Internaltip numbers $beforecount"
