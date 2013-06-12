#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

echo "[+] Setupping GLClient build environment"
sudo add-apt-repository ppa:chris-lea/node.js -y
sudo apt-get update -y
sudo apt-get install nodejs -y
sudo npm install -g grunt-cli

echo "[+] Setupping GLBackend build environment"
sudo apt-get install python-dev build-essential python-virtualenv python-pip python-stdeb -y

${DIR}/build-glclient.sh
${DIR}/build-glbackend.sh -n
