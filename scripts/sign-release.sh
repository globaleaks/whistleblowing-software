#!/bin/bash
# Script for adding package to repository and signing it
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

cd ${GLB_BUILD}/deb_dist

echo "[+] Adding deb package to the local repository"
dput local globaleaks*changes
mini-dinstall --batch

echo "[+] Copying GLClient package to ${WEB_DIR}"
cp ${GLCLIENT_DIR}/* ${WEB_DIR}

echo "[+] Signing Release"
gpg --default-key "$KEYID" --detach-sign -o Release.gpg.tmp ${REPO_DIR}/unstable/Release
mv Release.gpg.tmp ${REPO_DIR}/unstable/Release.gpg


