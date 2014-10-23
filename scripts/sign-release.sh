#!/bin/bash
# Script for adding package to repository and signing it
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEYID="24045008"
. ${DIR}/common_inc.sh

cd ${GLB_BUILD}/deb_dist

# GLBackedn deb package and GLClient build are pushed here
# in this later stage so that data is published only at the (good) end
# of the packaging activity
echo "[+] Adding deb package to the local repository"
dput local globaleaks*changes

# XXX why are we doing this? This seems quite hackish and it seems to be due to
# a bug inside of debuild. Are we sure we are using debuild properly?
# Previously builds did not require this hack to be present.
echo "[+] Signing Release"
gpg --default-key "${KEYID}" --detach-sign -o Release.gpg.tmp ${REPO_DIR}/unstable/Release
mv Release.gpg.tmp ${REPO_DIR}/unstable/Release.gpg
