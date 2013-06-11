#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

echo "[+] Setupping Packaging environment"
apt-get install mini-dinstall dput

echo "
[local]
method = local
incoming = ${REPO_DIR}/mini-dinstall/incoming" > ~/.dput.cf

echo "
architectures = all, i386
archivedir = ${REPO_DIR}
archive_style = flat
poll_time = 10
extra_keyrings = .gnupg/pubring.gpg
verify_sigs = 0
mail_to = info@globaleaks.org
generate_release = 1
release_origin = Hermes
release_codename = unstable
release_label = GlobaLeaks Debian Repository

[unstable]
release_suite = main" > ~/.mini-dinstall.conf

echo "[+] Setupping GLClient build environment"
add-apt-repository ppa:chris-lea/node.js -y
apt-get update -y
apt-get install nodejs -y
npm install -g grunt-cli

echo "[+] Setupping GLBackend build environment"
apt-get install python-dev build-essential python-virtualenv python-pip -y
wget -O requirements.txt "https://raw.github.com/globaleaks/GLBackend/master/requirements.txt"
pip install -r requirements.txt

${DIR}/build-testing-package.sh
