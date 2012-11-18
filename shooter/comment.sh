#!/bin/sh

SHOOTER="python shooter.py"

# get all the receiver tips
tip_list=`$SHOOTER A5 GET oid itip print-tip_gus | grep -v None`
for tip in $tip_list; do
    $SHOOTER T2 POST tip $tip
    if [ $? != 0 ]; then echo "\tError in T2 POST (comment)" && exit; fi
    echo "comment sent to $tip"
done
$SHOOTER T1 GET tip $tip verbose
if [ $? != 0 ]; then echo "\tError in T1 GET (tip)" && exit; fi

