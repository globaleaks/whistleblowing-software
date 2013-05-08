#!/bin/sh

usage()
{
cat << EOF

Usage: $0 options

   This script help in the creation of a new globaleaks instance.

	-d: domain (e.g.: subdomain.domain.tld)        [REQUIRED]

        -p: port (e.g.: 8082)                          [REQUIRED]

        -n: nodebase (e.g.: /var/subdomain.domain.tld) [OPTIONAL]

EOF
}

while getopts “hd:p:n” OPTION
do
     case $OPTION in
         h)
             usage
             exit
             ;;
         d)
             domain=$OPTARG
             ;;
         p)
             port=$OPTARG
             ;;
         n)
             nodebase=$OPTARG
             ;;
	 ?)
	     usage
             exit
	     ;;
	esac
done

if [ -z "$domain" ]; then
	echo "! MISSING ARGUMENT domain: you need to specify a -d domain"
        usage
        exit
fi

if [ -z "$port" ]; then
        echo "! MISSING ARGUMENT port: you need to specify a -p port"
        usage
        exit
fi

if [ -z "$nodebase"]; then
	nodebase="/var/$domain"
fi

echo "+ creating GlobaLeaks http://$domain:$port instance in directory $nodebase"

if [ -d $nodebase ]; then
	echo "! FAIL: directory $nodebase already present. debug please"
	exit
fi

mkdir -p $nodebase

if [ ! -d $nodebase ]; then
	echo "! FAIL: unable to create $nodebase, debug please"
	exit
fi

torrc="/etc/tor/torrc"
HSDIRpath="$nodebase/torhs"
HSDIRline="HiddenServiceDir $HSDIRpath"
HSPORTline="HiddenServicePort 80 127.0.0.1:$port"

if [ "`grep "$HSDIRline" $torrc`" ]; then
	echo "! FAIL: line $HSDIRline already present in $torrc, debug please"
	exit
fi

if [ "`grep "$HSPORTline" $torrc`" ]; then
        echo "! FAIL: line $HSPORTline already present in $torrc, debug please"
        exit
fi

echo "+ a new hidden service has been added to $torrc and binded at port $port"

echo $HSDIRline >> $torrc
echo $HSPORTline >> $torrc

chown globaleaks.globaleaks -R $nodebase

restartscript="$nodebase/restart-$domain.sh"
command="globaleaks -p $port -k 9 -l DEBUG -t -d -a 127.0.0.1,$domain -w $nodebase"

echo "su -c \"$command\" globaleaks" > $restartscript

chmod +x $restartscript

echo "SUCCESS:it's now possible to start/restart globaleaks by issuing $restartscript"
echo "\tto build the required GlobaLeaks Tor Hidden Service tor must be restarted also."
