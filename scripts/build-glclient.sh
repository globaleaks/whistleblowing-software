#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
GLCLIENT_GIT_REPO="https://github.com/globaleaks/GLClient.git"
GLOBALEAKS_DIR=/data/globaleaks
OUTPUT_DIR=$GLOBALEAKS_DIR/GLClient/glclient_build

usage()
{
cat << EOF
usage: ./${SCRIPTNAME} options

OPTIONS:
   -h      Show this message
   -v      To build a tagged release
   -y      To assume yes to all queries

EOF
}

ASSUME_YES=0
while getopts “hv:y” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    v)
      TAG=$OPTARG
      ;;
    y)
      ASSUME_YES=1
      ;;
    ?)
      usage
      exit
      ;;
    esac
done

mkdir -p $GLOBALEAKS_DIR $OUTPUT_DIR

build_glclient()
{
  if [ -d ${GLOBALEAKS_DIR}/GLClient ]; then
    echo "Directory ${GLOBALEAKS_DIR}/GLClient already present"
    echo "The build process needs a clean git clone of GLClient"
    if [ ${ASSUME_YES} -eq 0 ]; then
      read -n1 -p "Are you sure you want delete ${GLOBALEAKS_DIR}/GLClient? (y/n): "
      echo
      if [[ $REPLY != [yY] ]]; then
        echo "Exiting ..."
        exit
      fi
    fi
    echo "Removing directory ${GLOBALEAKS_DIR}"
    rm -rf ${GLOBALEAKS_DIR}/GLClient
  fi

  echo "[+] Cloning GLClient in ${GLOBALEAKS_DIR}"
  git clone $GLCLIENT_GIT_REPO ${GLOBALEAKS_DIR}/GLClient

  cd ${GLOBALEAKS_DIR}/GLClient
  git pull origin master
  GLCLIENT_REVISION=`git rev-parse HEAD | cut -c 1-8`

  if test $TAG; then
    git checkout $TAG
    GLCLIENT_REVISION=$TAG
  fi

  if [ -f $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.tar.gz ]; then
    echo "$OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.tar.gz already present"
    exit
  fi

  if [ -f $OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip ]; then
    echo "$OUTPUT_DIR/GLClient/glclient-${GLCLIENT_REVISION}.zip already present"
    exit
  fi

  echo "[+] Building GLClient"
  npm install -d
  grunt build

  mkdir -p $OUTPUT_DIR

  echo "[+] Creating compressed archives"
  mv build glclient-${GLCLIENT_REVISION}
  tar czf glclient-${GLCLIENT_REVISION}.tar.gz glclient-${GLCLIENT_REVISION}/
  cp glclient-${GLCLIENT_REVISION}.tar.gz $OUTPUT_DIR
  md5sum glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.tar.gz.md5.txt
  sha1sum glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIRglclient-${GLCLIENT_REVISION}.tar.gz.sha1.txt
  shasum -a 224 glclient-${GLCLIENT_REVISION}.tar.gz > $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.tar.gz.sha224.txt

  zip -r glclient-${GLCLIENT_REVISION}.zip glclient-${GLCLIENT_REVISION}/
  cp glclient-${GLCLIENT_REVISION}.zip $OUTPUT_DIR
  md5sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.zip.md5.txt
  sha1sum glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.zip.sha1.txt
  shasum -a 224 glclient-${GLCLIENT_REVISION}.zip > $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.zip.sha224.txt


  echo "[+] Copying GLClient package to /data/website/builds/"
  cp ${OUTPUT_DIR}/* /data/website/builds/


  rm -rf glclient-${GLCLIENT_REVISION}
}
build_glclient
echo "[+] All done!"
echo ""
echo "GLient hash: "
cat $OUTPUT_DIR/glclient-${GLCLIENT_REVISION}.zip.sha224.txt


