#!/bin/sh

SHOOTER="python shooter.py"

force_jobs() {
    $SHOOTER AB GET task delivery 
    if [ $? != 0 ]; then echo "\tError in AB (force delivery job)" && exit; fi
    $SHOOTER AB GET task notification
    if [ $? != 0 ]; then echo "\tError in AB (force notification job)" && exit; fi
}

# disable scheduled operations
$SHOOTER AB DELETE task alljobs

# force_jobs
# now we need to be the receiver with the tip, and vote pertinence.

tip_gus_list=`$SHOOTER AA GET dump rtip print-tip_gus`
if [ $? != 0 ]; then echo "\tError in AA GET (list of rtip)" && exit; fi
for tip_gus in $tip_gus_list; do
    $SHOOTER T1 PUT tip $tip_gus variation vote
    if [ $? != 0 ]; then echo "\tError in T1 PUT (expressing pertinence vote)" && exit; fi
    echo -n "."
done

# force_jobs
echo "\nwant to see InternalTip ? $SHOOTER AA GET dump itip verbose"
