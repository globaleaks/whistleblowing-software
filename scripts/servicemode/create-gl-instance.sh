#!/bin/sh

usage()
{
cat << EOF
usage: $0 options

   This script help in the creation of a new globaleaks instance.

	-d: domain (e.g.: subdomain.domain.tld)

        -p: port (e.g.: 8082)

        -n: nodebase (e.g.: /var/globaleaks/subdomain.domain.tld)

EOF
}

while getopts “h:d:p:n” OPTION
do
     case $OPTION in
         h)
             usage
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
	     ;;
	esac
done

if [ -z "$domain" ]; then
	echo "missing domain: you need to specify a -d domain"
        exit
fi

if [ -z "$port" ]; then
        echo "missing port: you need to specify a -p port"
        exit
fi

if [ -z "$nodebase"]; then
	nodebase="/var/$domain"
fi

echo "creating http://$domain"
echo "the internal port used would be $port"

echo "creating the GlobaLeaks directory: $nodebase"

if [ -d $nodebase ]; then
	echo "you're already a $nodebase directory. debug please"
	exit
fi

mkdir -p $nodebase

if [ ! -d $nodebase ]; then
	echo "Unable to create $nodebase, debug please"
	exit
fi

torrc="/etc/tor/torrc"
HSDIRpath="$nodebase/torhs"
HSDIRline="HiddenServiceDir $HSDIRpath"
HSPORTline="HiddenServicePort 80 127.0.0.1:$port"

if [ "`grep "$HSDIRline" $torrc`" ]; then
	echo "debug by hand please, in $torrc exists $HSDIRline"
	exit
fi

if [ "`grep "$HSPORTline" $torrc`" ]; then
        echo "debug by hand please, in $torrc exists $HSPORTline"
        exit
fi

echo "adding to $torrc the new hidden service binded at port $port"

echo $HSDIRline >> $torrc
echo $HSPORTline >> $torrc

chown globaleaks.globaleaks -R $nodebase

echo "restarting tor"
/etc/init.d/tor restart

echo "starting globaleaks instance"
echo "executing '$command' as user globaleaks"
restartscript="$nodebase/restart-$domain.sh"
command="globaleaks -p $port -k 9 --devel-mode -l DEBUG -t -d -a 127.0.0.1,$domain"
restartscript="$nodebase/restart-$domain.sh"
echo "su -c \"$command\" globaleaks" > $restartscript
chmod +x $restartscript

$restartscript
