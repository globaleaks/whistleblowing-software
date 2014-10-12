#!/bin/bash

if [ ! \( -r "$1" \) -o \( -z "$2" \) ]
    then
    echo "${BASH_SOURCE[0]} <client_revision> <backend_revision>"
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

TAGC=$1
TAGB=$2

${DIR}/build-glclient.sh -v $TAGC
${DIR}/build-glbackend.sh -v $TAGB
