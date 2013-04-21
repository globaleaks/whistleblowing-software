#!/bin/sh

usage()
{
cat << EOF
usage: $0 options

   This script help in the creation of a new globaleaks instance.

	-n: name (eg: randomleaks)

EOF
}

while getopts “h:l:c:b:n:” OPTION
do
     case $OPTION in
         h)
             usage
             ;;
         l)
	     logourl=$OPTARG
             ;;
         c)
	     clientbranch=$OPTARG
	     ;;
 	 b)
	     backendbranch=$OPTARG
	     ;;
	 n)
	     name=$OPTARG
	     ;;
	 ?)
	     usage
	     ;;
	esac
done


if [ -z "$name" ]; then
	echo "missing name: you need to specify a -n name"
	exit
fi

PORTFILE="port-count.index"

# getting the next available port
if ! [ -e "$PORTFILE" ]; then
	echo "someone has removed my $PORTFILE from $PWD"
	echo "please create a file in this directory, with the number of the latest TCP port used (eg: 8080)"
	exit
fi

port=`cat $PORTFILE`
port=$(($port+1))
echo $port > $PORTFILE

echo "creating http://$name.demo.globaleaks.org"
echo "the internal port used would be $port"

nodebase="$PWD/$name"
echo "creating the GlobaLeaks directory: $nodebase"

if [ -d $nodebase ]; then
	echo "you're already a $nodebase directory. debug please"
	exit
fi

mkdir $nodebase

if [ ! -d $nodebase ]; then
	echo "Unable to create $nodebase, debug please"
	exit
fi


chown globaleaks.globaleaks $nodebase
cd $nodebase

git clone https://github.com/globaleaks/GLBackend.git
git clone https://github.com/globaleaks/GLClient.git
# TODO, if an head or a branch different from master is specified, here need to be switched

HSDIRpath="$nodebase/torhs"
HSDIRline="HiddenServiceDir $HSDIRpath"
torrc="/etc/tor/torrc"

if [ "`grep $HSDIRpath $torrc`" ]; then
	echo "debug by hand please, in $torrc exists $HSDIRpath"
	exit
fi

echo "adding to $torrc the new hidden service to redirect at $port"

HSPORTline="HiddenServicePort 80 127.0.0.1:$port"

echo $HSDIRline >> $torrc
echo $HSPORTline >> $torrc

httpconf="/etc/apache2/sites-enabled/$name.demo.globaleaks.org"
echo "
<VirtualHost *:80>
	ServerName $name.demo.globaleaks.org
	ServerAlias $name.demo.globaleaks.org
	ServerAdmin info@globaleaks.org

	Redirect / http://$name.demo.globaleaks.org:$port/

	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory /var/www>
		Options FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>

	ErrorLog /var/log/apache2/$name.demo.globaleaks.org.error.log
	LogLevel warn
	CustomLog /var/log/apache2/$name.demo.globaleaks.org.access.log combined

</VirtualHost>
" > $httpconf

echo "created $httpconf for http://$name.demo.globaleaks.org:$port"

echo "restarting apache"
/etc/init.d/apache2 restart
echo "restarting tor"
/etc/init.d/tor restart
echo "starting globaleaks instance"

chown globaleaks.globaleaks -R $nodebase
cd GLBackend
command="$nodebase/GLBackend/bin/globaleaks -p $port -k 9 --devel-mode -l DEBUG -t -d -a 127.0.0.1,$name.demo.globaleaks.org"
echo "executing '$command' as user globaleaks"
su -c "$command" globaleaks

restartscript="../../restart-$name.sh"
echo "su -c \"$command\" globaleaks" > $restartscript
chmod +x $restartscript

ln -s $nodebase/GLBackend/workingdir ../nodedata 
