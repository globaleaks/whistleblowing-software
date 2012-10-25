#!/bin/sh

# this script, perform a loop of creation / update / get / remove

SHOOTER="python shooter.py"

for i in `seq 1 10`; do
    context_gus1=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
    if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

    context_gus2=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
    if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

    $SHOOTER A2 POST cid $context_gus1
    if [ $? != 0 ]; then echo "\tError context update " && exit; fi

    $SHOOTER A2 POST cid $context_gus2
    if [ $? != 0 ]; then echo "\tError context update " && exit; fi

    $SHOOTER A2 DELETE cid $context_gus1
    if [ $? != 0 ]; then echo "\tError context delete" && exit; fi

    $SHOOTER A2 DELETE cid $context_gus2
    if [ $? != 0 ]; then echo "\tError context delete" && exit; fi
done
