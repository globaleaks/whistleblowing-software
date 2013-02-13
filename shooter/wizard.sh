#!/bin/sh

SHOOTER="./shooter.py"

# the node
$SHOOTER A1 PUT

one=`$SHOOTER A2 POST raw None print-context_gus`
if [ $? != 0 ]; then echo "\tError context (base) creation: $one " && exit; fi

#two=`$SHOOTER A2 POST raw None print-context_gus variation 1`
two=`$SHOOTER A2 POST raw None print-context_gus`
if [ $? != 0 ]; then echo "\tError context (1) creation: $two" && exit; fi

echo "created two contexts: $one $two"

rcvr1=`$SHOOTER A4 POST print-receiver_gus raw \"$one\",\"$two\"`
if [ $? != 0 ]; then echo "\tError receiver1 creation " && exit; fi

rcvr2=`$SHOOTER A4 POST print-receiver_gus raw \"$one\",\"$two\" variation 1`
if [ $? != 0 ]; then echo "\tError receiver2 creation " && exit; fi

rcvr3=`$SHOOTER A4 POST print-receiver_gus raw \"$one\",\"$two\" variation 2`
if [ $? != 0 ]; then echo "\tError receiver3 creation " && exit; fi

rcvr4=`$SHOOTER A4 POST print-receiver_gus raw \"$one\",\"$two\" variation 3`
if [ $? != 0 ]; then echo "\tError receiver4 creation " && exit; fi

rcvr5=`$SHOOTER A4 POST print-receiver_gus raw \"$one\",\"$two\" variation 4`
if [ $? != 0 ]; then echo "\tError receiver5 creation " && exit; fi

echo "created five receiver in context 1 and 2: $rcvr1 $rcvr2 $rcvr3 $rcvr4 $rcvr5"

