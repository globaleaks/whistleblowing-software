#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

echo "[+] Setupping GLClient and GLBackend build environments"

if [ ! -f ${DIR}/.environment_setupped ]; then
    sudo -i add-apt-repository ppa:chris-lea/node.js -y
    sudo -i apt-get update -y
    sudo -i apt-get install nodejs -y
    sudo -i npm install -g grunt-cli
    sudo -i apt-get install python-dev build-essential python-virtualenv python-pip python-stdeb devscripts -y
    touch ${DIR}/.environment_setupped
fi

${DIR}/build-glclient.sh
${DIR}/build-glbackend.sh -n
