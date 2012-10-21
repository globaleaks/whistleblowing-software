#!/bin/sh

SHOOTER="python shooter.py"

submission_id=`$SHOOTER U2 print-submission_id`
$SHOOTER U3 GET sid $submission_id
$SHOOTER U3 POST sid $submission_id
$SHOOTER U4 sid $submission_id
