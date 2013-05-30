#!/bin/sh
# Script for adding package to repository and signing it
CWD=`pwd`
REPO_DIR='/data/deb/unstable/'
GLOBALEAKS_DIR=/data/globaleaks
OUTPUT_DIR='/data/website/builds/'

cd $GLOBALEAKS_DIR/glbackend_build

echo "[+] Adding to local repository"
dput local globaleaks*changes
mini-dinstall --batch

echo "[+] Signing Release"
gpg --default-key "$KEYID" --detach-sign -o Release.gpg.tmp ${REPO_DIR}/Release
mv Release.gpg.tmp ${REPO_DIR}/Release.gpg

echo "[+] Copying GLClient package to ${OUTPUT_DIR}"
cp ${GLOBALEAKS_DIR}/glclient_build/* ${OUTPUT_DIR}
