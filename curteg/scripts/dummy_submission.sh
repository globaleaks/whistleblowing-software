#!/bin/sh

CURTEG="python ../curteg.py"

# TODO: query U1, get context ID, use context ID to obtain submission ID
submission_id=`$CURTEG U2 print-submission_id`
$CURTEG U3 GET sid $submission_id
$CURTEG U3 POST sid $submission_id
$CURTEG U4 sid $submission_id
