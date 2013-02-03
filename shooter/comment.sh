#!/bin/sh

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

dt "0" "D2 DELETE task alljobs" "Disabling all the scheduled jobs"

dt "1" "D1 GET dump rtip print-tip_gus" "dumping receiver tips, after tests"
tip_list=$ret

echo -n "Receiver comments: "
for tip in $tip_list; do
    dt "2x" "T2 POST tip $tip" "posting comment in tip $tip"
done

dt "3" "D1 GET dump wtip print-receipt" "dumping whistleblower tips"
receipt_list=$ret

echo -n "WhistleBlower comments: "
for wb_receipt in $receipt_list; do
    dt "4x" "T2 POST tip $wb_receipt variation wb" "posting comment as whistleblower with $wb_receipt"
done

dt "5" "D2 GET task notification" "forcing comments notification"
