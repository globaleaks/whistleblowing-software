#!/bin/bash
# Script for adding package to repository and signing it
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEYID="24045008"
. ${DIR}/common_inc.sh

cd ${GLB_BUILD}/deb_dist

echo "[+] Adding deb package to the local repository"
dput local globaleaks*changes

if [ -d ${GLCLIENT_DIR} ]; then
  echo "[+] Copying GLClient package to ${WEB_DIR}"
  cp ${GLCLIENT_DIR}/* ${WEB_DIR}
fi
