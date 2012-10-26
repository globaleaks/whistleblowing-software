#!/bin/sh

SHOOTER="python shooter.py"

one=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

two=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

three=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

four=`$SHOOTER A2 PUT cid c_OOOOOOOOOOOOOOOOOOOO print-context_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

rcvr=`$SHOOTER A3 PUT rid r_AAAAAAAAAAAAAAAAAAAA print-receiver_gus`
if [ $? != 0 ]; then echo "\tError context creation " && exit; fi

echo "created four contexts: $one $two $three $four"
echo "created one receiver: $rcvr"

