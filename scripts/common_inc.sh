#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
GLBACKEND_GIT_REPO="https://github.com/globaleaks/GLBackend.git"
GLCLIENT_GIT_REPO="https://github.com/globaleaks/GLClient.git"
ROOT_DIR=$( readlink -m ${DIR}/../../)
GLBACKEND_DIR=$( readlink -m ${ROOT_DIR}/GLBackend)
GLCLIENT_DIR=$( readlink -m ${ROOT_DIR}/GLClient)
GLB_BUILD=$( readlink -m ${GLBACKEND_DIR}/glbackend_build)
GLC_BUILD=$( readlink -m ${GLCLIENT_DIR}/glclient_build)

REPO_DIR='/data/deb'
WEB_DIR='/data/website/builds'

if test ${GLOBALEAKS_BUILD_ENV}; then
  BUILD_DIR=${GLOBALEAKS_BUILD_ENV}
else
  BUILD_DIR='/data/globaleaks'
fi

set -e
