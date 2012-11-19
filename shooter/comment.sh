#!/bin/sh

SHOOTER="python shooter.py"

# get all the receiver tips
tip_list=`$SHOOTER A5 GET oid itip print-tip_gus | grep -v None`
for tip in $tip_list; do
    $SHOOTER T2 POST tip $tip
    if [ $? != 0 ]; then echo "\tError in T2 POST (Receiver Comment)" && exit; fi
    echo "comment sent to $tip"
done

receipt_list=`$SHOOTER A5 GET oid wtip print-receipt`
for wb_receipt in $receipt_list; do
    $SHOOTER T2 POST tip $wb_receipt variation wb
    if [ $? != 0 ]; then echo "\tError in T2 POST (WhistleBlower Comment)" && exit; fi
    echo "comment sent to $wb_receipt"
done

# get the latest tip as visible check
$SHOOTER T1 GET tip $tip verbose
if [ $? != 0 ]; then echo "\tError in T1 GET (tip)" && exit; fi

echo "forcing comments notification"
$SHOOTER A6 GET oid notification

