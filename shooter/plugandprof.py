#!/bin/sh
# Just a simple operational tested over plugins and profiles, from the APIs:

# 'A6_GET':'GET_/admin/plugin',
# 'A7_POST':'POST_/admin/profile',
# 'A7_GET':'GET_/admin/profile',
# 'A8_GET':'GET_/admin/profile/@PID@',
# 'A8_PUT':'PUT_/admin/profile/@PID@',
# 'A8_DELETE':'DELETE_/admin/profile/@PID@',

SHOOTER="./shooter.py"

$SHOOTER D2 DELETE task alljobs
$SHOOTER D1 GET dump plugins # list commonly get with A6

context_list=`$SHOOTER D1 GET dump contexts print-context_gus`
for context_gus in $context_list; do

    # create notification profile
    profile_gus=`$SHOOTER A7 POST cid $context_gus variation mail print-profile_gus`
    $SHOOTER A8 PUT cid $context_gus pid $profile_gus variation mail 

    # tested but removed from the loop:
    # $SHOOTER A7 GET verbose
    # $SHOOTER A8 GET pid $profile_gus verbose
    # $SHOOTER A8 DELETE pid $profile_gus verbose

    # create fileprocess profile
    profile_gus=`$SHOOTER A7 POST cid $context_gus variation content print-profile_gus`

    # create delivery profile
    profile_gus=`$SHOOTER A7 POST cid $context_gus variation download print-profile_gus`
done


