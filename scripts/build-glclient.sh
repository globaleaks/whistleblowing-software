#!/bin/bash
CWD=`pwd`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
GLCLIENT_GIT_REPO="https://github.com/globaleaks/GLClient.git"
GLOBALEAKS_DIR=~/
OUTPUT_DIR=/data/website/builds/

if [ "$1" = "-h" ]; then
  echo "Usage: ./${SCRIPTNAME} [glclient target tag or rev]"
  exit
fi

GLCLIENT_TAG=$1

mkdir $OUTPUT_DIR/GLClient

if [ ! -d ${GLOBALEAKS_DIR}/GLClient ]; then
  echo "[+] Cloning GLClient in ${GLOBALEAKS_DIR}"
  git clone $GLCLIENT_GIT_REPO ${GLOBALEAKS_DIR}/GLClient
fi

build_glclient()
{
  echo "[+] Updating GLClient"
  cd ${GLOBALEAKS_DIR}/GLClient
  git pull origin master
  GLCLIENT_REVISION=`git rev-parse HEAD | cut -c 1-8`

  if test $GLCLIENT_TAG; then
    git checkout $GLCLIENT_TAG
    $GLCLIENT_REVISION=$GLCLIENT_TAG
  fi

  echo "[+] Building GLClient"
  npm install -d
  grunt build

  echo "[+] Creating compressed archives"
  mv build glclient-${GLCLIENT_REVISION}
  tar czf glclient-${GLCLIENT_REVISION}.tar.gz glclient-${GLCLIENT_REVISION}/
  md5sum glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.tar.gz.md5.txt
  sha1sum glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.tar.gz.sha1.txt
  shasum -a 224 glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.tar.gz.sha224.txt

  zip -r glclient-${GLCLIENT_REVISION}.zip glclient-${GLCLIENT_REVISION}/
  md5sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.md5.txt
  sha1sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.sha1.txt
  shasum -a 224 glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.sha224.txt

  mv glclient-${GLCLIENT_REVISION}.tar.gz $OUTPUT_DIR/GLClient
  mv glclient-${GLCLIENT_REVISION}.zip $OUTPUT_DIR/GLClient
  rm -rf glclient-${GLCLIENT_REVISION}
  cd $CWD
}
build_glclient
echo "[+] All done!"
echo ""
echo "GLient hash: "
cat $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.sha224.txt


