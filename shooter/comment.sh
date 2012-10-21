#!/bin/sh

SHOOTER="python shooter.py"

if [ -n "$1" ]; then
    $SHOOTER T1 GET tip $1 
    if [ $? != 0 ]; then echo "\tError in T1 GET" && exit; fi
    $SHOOTER T2 POST tip $1
    if [ $? != 0 ]; then echo "\tError in T2 POST" && exit; fi
    $SHOOTER T1 GET tip $1 verbose
    if [ $? != 0 ]; then echo "\tError in T1 GET (second check)" && exit; fi
else
    echo "you need to specify an active tip (no receipt!)"
fi

