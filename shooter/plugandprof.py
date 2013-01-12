#!/bin/sh
# Just a simple operational tested over plugins and profiles, from the APIs:

# 'A6_GET':'GET_/admin/plugin',
# 'A7_POST':'POST_/admin/profile',
# 'A7_GET':'GET_/admin/profile',
# 'A8_GET':'GET_/admin/profile/@PID@',
# 'A8_PUT':'PUT_/admin/profile/@PID@',
# 'A8_DELETE':'DELETE_/admin/profile/@PID@',

# dt "identificative number" "portion of command line" "description" "assertion description"
dt() {
    dumpfile="/tmp/dumptest_$1"
    echo > $dumpfile

    echo -n "$1) $3 ..."
    ret=`$SHOOTER $2`
    if [ $? != 0 ]; then 
        echo "\tError [$2]" 
        echo "Error [$2]\n\n$ret" >> $dumpfile
        echo "saved error in $dumpfile"
        exit
    fi
    echo " done."

    echo "$3" >> $dumpfile
    echo "$2" >> $dumpfile
    if [ ! -z "$4" ]; then
        echo $4 >> $dumpfile
    fi
    echo "\n\n" >> $dumpfile

    $SHOOTER D1 GET dump count verbose >> $dumpfile
}


SHOOTER="./shooter.py"

dt "1" "D2 DELETE task alljobs" "blocking scheduled task"
dt "2" "D1 GET dump plugins" "list plugins with plugin" 
plugin_list=$ret
dt "3" "A6 GET" "list plugins with Admin interface"


# Create context 1- 
dt "4" "A2 POST raw None print-context_gus" "Create a Context 1"
context_one=$ret

# Create context 2- 
dt "5" "A2 POST raw None print-context_gus" "Create a Context 2" 
context_two=$ret

# Receiver 1
dt "6" "A4 POST print-receiver_gus raw \"$context_two\",\"$context_one\"" "Create a receiver 1"
receiver_one=$ret

# Receiver 2
dt "7" "A4 POST print-receiver_gus raw \"$context_two\",\"$context_one\"" "Create a receiver 2"
receiver_two=$ret

# Create valid tip to access receiver configuration

# Submission open context 1
dt "S" "U2 POST cid $context_one print-submission_gus" "opening a new submission 1"
submission_gus_1=$ret

# Submission Finalize context 1
dt "F" "U3 PUT cid $context_one sid $submission_gus_1 raw \"\" print-receipt" "completing submission and getting receipt 1"
receipt_1=$ret

# Submission open context 2
dt "S" "U2 POST cid $context_two print-submission_gus" "opening a new submission 1"
submission_gus_2=$ret

# Submission Finalize context 2
dt "F" "U3 PUT cid $context_one sid $submission_gus_2 raw \"\" print-receipt" "completing submission and getting receipt 1"
receipt=$ret

# force tip creation
dt "ivivvd" "D2 GET task tip" "Forcing tip creation asyncronous operation"

dt "L" "D1 GET dump rtip print-tip_gus" "acquiring created tip_gus"
tip_gus_list=$ret
echo $tip_gus_list

# create notification profile 1
dt "8" "A7 POST cid $context_one variation mail print-profile_gus" "create profile mail for c1"
profile_mail_1=$ret

# enable local download 1
dt "8" "A7 POST cid $context_one variation mail print-profile_gus" "create profile download for c1"
profile_download_1=$ret

# enable contect file processing 1
dt "9" "A7 POST cid $context_one variation mail print-profile_gus" "create profile contet for c1"
profile_content_1=$ret

# 'R2_GET':'GET_/receiver/@TIP@/profile',
# 'R3_GET':'GET_/receiver/@TIP@/profileconf',
# 'R3_POST':'POST_/receiver/@TIP@/profileconf',
# 'R4_GET':'GET_/receiver/@TIP@/profileconf/@CFGID@',
# 'R4_PUT':'PUT_/receiver/@TIP@/profileconf/@CFGID@',
# 'R4_DELETE':'DELETE_/receiver/@TIP@/profileconf/@CFGID@'

# this loop use the Tip auth, for configure in both the tip owner (receiver1 and 2)
# a mail settings, associated to the context_one.

# A tip associated to context_two, VALIDATE the receiver also if is operating on context_one
# related settings. Tip, in this very case, work just as authentication method for the
# receiver. Welcome Token would be checked in this operation.
echo "Starting the operation AUTHORIZED by Tip auth token (or welcome token)\n"
for tip_gus in $tip_gus_list; do

    dt "A_13" "R2 GET tip $tip_gus verbose" "list the available profiles"
    dt "A_14" "R3 GET tip $tip_gus verbose" "list the present receiver conf"

    dt "A_15" "R3 POST tip $tip_gus cid $context_one pid $profile_mail_1 raw vecna@delirandom.net variation mail print-config_id" "create a new receiver conf (mail)"
    config_id_mail=$ret
    dt "A_16" "R4 PUT tip $tip_gus cfgid $config_id_mail cid $context_one pid $profile_mail_1 variation mail raw vecna@globaleaks.org" "update the mail conf"

    dt "A_17" "R3 POST tip $tip_gus cid $context_one pid $profile_download_1 variation download raw ciaokeyciao print-config_id" "create a new receiver conf (download)"
    config_id_download=$ret
    dt "A_18" "R4 PUT tip $tip_gus cfgid $config_id_download cid $context_one pid $profile_download_1 variation download raw oiaoiaoia" "update the download conf"

    # Force tip schedule notification
    dt "A_19" "D2 GET task notification" "Forcing tip notificaion asyncronous operation"
    dt "A_20" "R4 DELETE tip $tip_gus cfgid $config_id verbose" "delete the conf"

    echo "Completed operation authorized with tip $tip_gus\n"
done

echo "Done first configuration loop, press enter"
read x

# create notification profile 2
dt "21" "A7 POST cid $context_two variation mail print-profile_gus" "create profile mail for c1"
profile_mail_2=$ret

# enable local download 2
dt "22" "A7 POST cid $context_two variation mail print-profile_gus" "create profile download for c1"
profile_download_2=$ret

# enable contect file processing 2
dt "23" "A7 POST cid $context_two variation mail print-profile_gus" "create profile contet for c1"
profile_content_2=$ret


