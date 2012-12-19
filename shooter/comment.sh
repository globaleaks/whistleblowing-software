#!/bin/sh

SHOOTER="python shooter.py"

# disable scheduled operations
$SHOOTER AB DELETE oid alljobs

# get all the receiver tips
tip_list=`$SHOOTER AA GET oid rtip print-tip_gus | grep -v None`
if [ $? != 0 ]; then echo "\tError in AA GET (Receiver Tip GUS)" && exit; fi
echo -n "Receiver comments: "
for tip in $tip_list; do
    $SHOOTER T2 POST tip $tip
    if [ $? != 0 ]; then echo "\tError in T2 POST (Receiver Comment)" && exit; fi
    echo -n "."
done
echo " done."

receipt_list=`$SHOOTER AA GET oid wtip print-receipt`
if [ $? != 0 ]; then echo "\tError in A5 GET (WhistleBlower Receipts)" && exit; fi
echo -n "WhistleBlower comments: "
for wb_receipt in $receipt_list; do
    $SHOOTER T2 POST tip $wb_receipt variation wb
    if [ $? != 0 ]; then echo "\tError in T2 POST (WhistleBlower Comment)" && exit; fi
    echo -n "."
done
echo " done."

# get the latest tip as visible check
$SHOOTER T2 GET tip $tip verbose
if [ $? != 0 ]; then echo "\tError in T1 GET (tip)" && exit; fi

echo "forcing comments notification"
$SHOOTER A6 GET oid notification
