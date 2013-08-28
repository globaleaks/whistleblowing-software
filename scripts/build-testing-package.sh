#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

usage()
{
cat << EOF
usage: ./${SCRIPTNAME} options

OPTIONS:
   -h   Show this message
   -c   To build a specific client version
   -b   To build a specific backend version
   -y   Assume 'yes' to all questions
EOF
}

AUTOYES=0
while getopts “hc:b:y” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    c)
      TAGC=$OPTARG
      ;;
    b)
      TAGB=$OPTARG
      ;;
    y)
      AUTOYES=1
      ;;
    ?)
      usage
      exit
      ;;
    esac
done

echo "[+] Setupping GLClient and GLBackend build environments"

if [ ! -f ${DIR}/.environment_setupped ]; then
    sudo -i add-apt-repository ppa:chris-lea/node.js -y
    sudo -i apt-get update -y
    sudo -i apt-get install nodejs -y
    sudo -i npm install -g grunt-cli bower
    sudo -i apt-get install python-dev build-essential python-virtualenv python-pip python-stdeb devscripts -y
    touch ${DIR}/.environment_setupped
fi

if [ $AUTOYES -eq 1 ]; then
  OPTS="-y"
else
  OPTS=""
fi

if test $TAGC; then
  ${DIR}/build-glclient.sh -v $TAGC $OPTS
else
  ${DIR}/build-glclient.sh $OPTS
fi

if test $TAGB; then
  ${DIR}/build-glbackend.sh -v $TAGB -n $OPTS
else
  ${DIR}/build-glbackend.sh -n $OPTS
fi
