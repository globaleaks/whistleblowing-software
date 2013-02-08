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


dt "1" "D2 DELETE task alljobs" "Disabling all the scheduled jobs"
dt "2" "D1 GET dump rtip print-tip_gus" "dumping tip_gus available"
tip_gus_list=$ret

for tip_gus in $tip_gus_list; do
    dt "\t3+" "T1 PUT tip $tip_gus variation vote" "expressing positive vote"
done

dt "4" "D2 GET task delivery" "Forcing delivery asyncronous operation"
dt "5" "D2 GET task notification" "Forcing notification asyncronous operation"

