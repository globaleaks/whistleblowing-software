#!/bin/sh

SHOOTER="./shooter.py"

#
# This script wrap the shooter.py script. do not include any of the globaleaks files


# disable scheduled operations
$SHOOTER AB DELETE task alljobs

context_list=`$SHOOTER AA GET dump context print-context_gus`
if [ $? != 0 ]; then echo "\tError in AA GET" && exit; fi

beforecount=`$SHOOTER AA GET dump itip print-elements`
if [ $? != 0 ]; then echo "\tError in AA GET" && exit; fi
echo "Internaltip numbers $beforecount"

for context_gus in $context_list; do
    submission_gus=`$SHOOTER U2 POST cid $context_gus print-submission_gus`
    if [ $? != 0 ]; then echo "\tError in U2 POST" && exit; fi
    echo "context $context_gus, submission token: $submission_gus"

    receipt=`$SHOOTER U3 PUT cid $context_gus sid $submission_gus print-receipt`
    if [ $? != 0 ]; then echo "\tError in U3 PUT" && exit; fi
    echo "context $context_gus, receipt $receipt"
done

# Force tip schedule creation
`./shooter.py AB GET task tip`
if [ $? != 0 ]; then echo "\tError in AB GET" && exit; fi

beforecount=`$SHOOTER AA GET dump itip print-elements`
if [ $? != 0 ]; then echo "\tError in AA GET" && exit; fi
echo "Internaltip numbers $beforecount"
