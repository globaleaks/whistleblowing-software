#!/bin/sh

# this script, perform a loop of creation / update / get / remove in context
# creation / update / get / delete of receiver, and get info from the node.

SHOOTER="python shooter.py"

cntx_gus1=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

cntx_gus2=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

echo " created $cntx_gus1 and $cntx_gus2"

$SHOOTER A2 POST cid $cntx_gus1
if [ $? != 0 ]; then echo "\tError context update " && exit; fi

$SHOOTER A2 POST cid $cntx_gus2
if [ $? != 0 ]; then echo "\tError context update " && exit; fi

echo " updated $cntx_gus1 and $cntx_gus2"

rcvr1=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus raw \"$cntx_gus1\",\"$cntx_gus2\"`
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi

rcvr2=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus raw \"$cntx_gus1\",\"$cntx_gus2\"`
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi

echo " receiver $rcvr1 and $rcvr2 created"

$SHOOTER A3 POST rid $rcvr1 raw \"$cntx_gus1\"
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi

$SHOOTER A3 POST rid $rcvr2 raw \"$cntx_gus2\"
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi

echo " modified receiver $rcvr1 in $cntx_gus1, and $rcvr2 in $cntx_gus2"

$SHOOTER A2 DELETE cid $cntx_gus1
if [ $? != 0 ]; then echo "\tError context delete" && exit; fi

$SHOOTER A2 DELETE cid $cntx_gus2
if [ $? != 0 ]; then echo "\tError context delete" && exit; fi

echo " deleted $cntx_gus1, $cntx_gus2"

$SHOOTER A3 DELETE rid $rcvr1 
if [ $? != 0 ]; then echo "\tError receiver delete " && exit; fi

$SHOOTER A3 DELETE rid $rcvr2
if [ $? != 0 ]; then echo "\tError receiver delete " && exit; fi

echo " deleted $rcvr1, $rcvr2"
