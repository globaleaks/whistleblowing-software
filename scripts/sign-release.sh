#!/bin/sh
# Script for adding package to repository and signing it
CWD=`pwd`
REPO_DIR='/data/deb/unstable/'

cd ${GLOBALEAKS_DIR}/GLBackend/dist

echo "[+] Adding to local repository"
dput local globaleaks*changes
mini-dinstall --batch

echo "[+] Signing Release"
gpg --default-key "$KEYID" --detach-sign -o Release.gpg.tmp ${REPO_DIR}/Release
mv Release.gpg.tmp ${REPO_DIR}/Release.gpg

cd $CWD

rm -rf ${GLOBALEAKS_DIR}/GLBackend/dist
