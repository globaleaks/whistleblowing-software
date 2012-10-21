#!/bin/sh

SHOOTER="python shooter.py"


if [ -n "$1" ]; then
    $SHOOTER T1 GET tip $1 
    $SHOOTER T2 POST tip $1
    $SHOOTER T1 GET tip $1 verbose
fi

