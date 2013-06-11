#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

${DIR}/build-glclient.sh
${DIR}/build-glbackend.sh -n
