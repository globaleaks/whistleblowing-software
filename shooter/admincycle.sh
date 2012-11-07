#!/bin/sh

# this script, perform a loop of creation / update / get / remove in context
# creation / update / get / delete of receiver, and get info from the node.

SHOOTER="python shooter.py"

echo -n "testing context creation..."
cntx_gus1=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi
cntx_gus2=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi
echo " created 1= $cntx_gus1 and 2= $cntx_gus2"

echo -n "testing context update..."
$SHOOTER A2 POST cid $cntx_gus1
if [ $? != 0 ]; then echo "\tError context update " && exit; fi
$SHOOTER A2 POST cid $cntx_gus2
if [ $? != 0 ]; then echo "\tError context update " && exit; fi
echo " updated 1= $cntx_gus1 and 2= $cntx_gus2"

echo -n "testing receiver creation..."
rcvr1=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus raw \"$cntx_gus1\"`
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi
rcvr2=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus raw \"$cntx_gus2\"`
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi
rcvr3=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus raw \"$cntx_gus1\",\"$cntx_gus2\"`
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi
echo " receiver 1= $rcvr1, 2= $rcvr2, 3= $rcvr3 created"

echo -n "testing receiver update..."
$SHOOTER A3 POST rid $rcvr3 raw \"$cntx_gus2\"
if [ $? != 0 ]; then echo "\tError receiver creation " && exit; fi
echo " modified receiver: 1= $rcvr1 in 1= $cntx_gus1, 2= $rcvr2 and 3= $rcvr3 in 2= $cntx_gus2"


echo "testing effectiveness of the previous operations... (dumped files)"
# context 1 need to have the languages specified in the PUT only
# context 2 need to have both the languages 
# context 1 has only one receiver ($rcvr), context 2 has two receiver ($rcvr2 and $rcvr3)
$SHOOTER A2 GET cid $cntx_gus1 verbose > /tmp/ctx_one
$SHOOTER A2 GET cid $cntx_gus2 verbose > /tmp/ctx_two
# automatic checks in TODO :P

if [ -n "$1" ] && [ "$1" = "keep" ]; then
    echo "keep option detected, creation not removed"
    exit
fi


echo -n "testing context delete..."
$SHOOTER A2 DELETE cid $cntx_gus1
if [ $? != 0 ]; then echo "\tError context delete" && exit; fi
$SHOOTER A2 DELETE cid $cntx_gus2
if [ $? != 0 ]; then echo "\tError context delete" && exit; fi
echo " deleted 1= $cntx_gus1, 2= $cntx_gus2"

echo -n "testing receiver delete..."
$SHOOTER A3 DELETE rid $rcvr1 
if [ $? != 0 ]; then echo "\tError receiver delete " && exit; fi
$SHOOTER A3 DELETE rid $rcvr2
if [ $? != 0 ]; then echo "\tError receiver delete " && exit; fi
echo " deleted 1= $rcvr1, 2= $rcvr2"

# now receiver 3 would be remained without a context ?
$SHOOTER A3 GET rid $rcvr3 verbose > /tmp/rcvr_three
if [ $? != 0 ]; then echo "\tError receiver verification" && exit; fi

echo "/tmp/ctx_one /tmp/ctx_two and /tmp/rcvr_three contains some status checks"
