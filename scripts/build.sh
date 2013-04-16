#!/bin/sh
CWD=`pwd`
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
GLBACKEND_GIT_REPO="https://github.com/globaleaks/GLBackend.git"
GLCLIENT_GIT_REPO="https://github.com/globaleaks/GLClient.git"

if [ "$#" -ne 2 ]; then
  echo "Usage: ./${SCRIPTNAME} [repository path] [output dir] (optional) [glclient target tag or rev] [glbackend target tag]"
  echo "repository path: is the path to a copy of the GLClient and GLBackend git repositories"
  exit
fi
GLOBALEAKS_DIR=$1
OUTPUT_DIR=$2

if [ "$#" -eq 4 ]; then
  GLCLIENT_TAG=$3
  GLBACKEND_TAG=$4
fi

mkdir $OUTPUT_DIR/GLClient
mkdir $OUTPUT_DIR/GLBackend

if [ ! -d ${GLOBALEAKS_DIR}/GLBackend ]; then
  echo "[+] Cloning GLBackend in ${GLOBALEAKS_DIR}"
  git clone $GLBACKEND_GIT_REPO ${GLOBALEAKS_DIR}/GLBackend
fi

if [ ! -d ${GLOBALEAKS_DIR}/GLClient ]; then
  echo "[+] Cloning GLClient in ${GLOBALEAKS_DIR}"
  git clone $GLBACKEND_GIT_REPO ${GLOBALEAKS_DIR}/GLClient
fi

echo "[+] Updating GLBackend"
cd ${GLOBALEAKS_DIR}/GLBackend
git pull origin master
GLBACKEND_REVISION=`git rev-parse HEAD | cut -c 1-8`

if test $GLBACKEND_TAG; then
  git checkout $GLBACKEND_TAG
  $GLBACKEND_REVISION=$GLBACKEND_TAG
fi

echo "[+] Building GLBackend"
python setup.py bdist sdist
cd $CWD

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

zip -r glclient-${GLCLIENT_REVISION}.zip glclient-${GLCLIENT_REVISION}/
md5sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.md5.txt
sha1sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip.sha1.txt

mv glclient-${GLCLIENT_REVISION}.tar.gz $OUTPUT_DIR/GLClient
mv glclient-${GLCLIENT_REVISION}.zip $OUTPUT_DIR/GLClient
rm -rf glclient-${GLCLIENT_REVISION}
cd $CWD

echo "[+] All done!"

