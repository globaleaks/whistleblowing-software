#!/bin/sh

# this script, perform an emulation of the administrator life activity

SHOOTER="./shooter.py"

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



# disable scheduled operations
dt "1" "D2 DELETE task alljobs" "Disabling all the scheduled jobs"

# Create first context
dt "2" "A2 POST raw None print-context_gus" "Creating Context 1"
context_one=$ret

# Create first receiver.
dt "3" "A4 POST print-receiver_gus raw None" "Creating Receiver 1"
receiver_one=$ret

# Add the receiver to the context
dt "4" "A5 PUT rid $receiver_one raw \"$context_one\"" "Update Receiver 1 and assign to Context 1"

# Start a test submission to the context
dt "5" "U2 POST cid $context_one print-submission_gus" "Opening a submission to the context"
submission_gus=$ret

# update the submission with the receiver selection (ignored, in this context
# configuration, the receivers are selected by default and can't be changed by
# whistleblower will). Finalize the submission.
dt "6" "U3 PUT cid $context_one raw None sid $submission_gus print-receipt" "Submission completed"

# DEBUG operation: Force tip schedule execution (create receivertip)
dt "7" "D2 GET task tip verbose" "Forced tip creation for receiver" "assertion: one itip, wtip, receivertip, receiver, context"

# Removing the context with a receiver and a tip assigned
dt "8" "A3 DELETE cid $context_one" "Removing Context 1" "zero tip, context. one receiver, with zero context"

# Create a new context - verify receiver orphanage
dt "9" "A2 POST raw None print-context_gus" "Create a Context 2" "one context without receiver, one receiver without context"
context_two=$ret

# Take receiver_one and assign to the context_two
dt "10" "A3 PUT cid $context_two raw \"$receiver_one\"" "Update the Context 2 and assign Receiver 1"

# Create a new receiver, assign the new receiver to the context
# Note: from a context can be assigned a new receiver, and from a 
# receiver can be assignede to a context. the operations effect are the same
dt "11" "A4 POST print-receiver_gus raw \"$context_two\"" "Create a second receiver assigned to Context 2"
receiver_two=$ret

# Perform a new submission, aimed for both the receivers
dt "12" "U2 POST cid $context_two print-submission_gus" "new Submission to Context 2"
submission_gus=$ret

# update the submission with the receiver and finalize them
dt "13" "U3 PUT cid $context_two raw None sid $submission_gus print-receipt" "Submission 2 completed"
receipt=$ret

# DEBUG operation: Force tip schedule execution (create receivertip)
dt "14" "D2 GET task tip verbose" "Force ReceiverTip creation event"

# DEBUG operation: get the receivers tip_gus
# (These information use to be notified, but for this test we obtain 
# these by the debug interface)

dt "15" "D1 GET dump rtip print-tip_gus" "Getting the list of ReceiverTips"
tip_gus_list=$ret

for tip_gus in $tip_gus_list; do

    # receiver1 and receiver2: comment
    dt "16x" "T2 POST tip $tip_gus" "\tCommenting Tip as receiver"

    # receiver1 and receiver2: express a vote
    dt "17x" "T1 PUT tip $tip_gus variation vote" "\tVoting Tip as receiver"

done

# Make a whistleblower comment
dt "18" "T2 POST tip $receipt variation wb" "Commenting WhistleBlower Tip"

# Read all the comments
echo "[+] Checks comments presence (has to be 3):"
$SHOOTER D1 GET dump comment print-comment_elements

# admin delete Receiver1 from the node
dt "19" "A5 DELETE rid $receiver_one" "Deleting Receiver1 from the Node" "three comments, one receiver tip, and context_two with only receiver_two"

# Delete context
dt "20" "A3 DELETE cid $context_two" "Deleting Context2 from the Node" "remain only one receiver"

# Delete the last receiver
dt "21" "A5 DELETE rid $receiver_two" "Deleting Receiver2 from the Node" "zero elements at all"

