#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. ${DIR}/common_inc.sh

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

while getopts “hv:” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    v)
      TAG=$OPTARG
      ;;
    ?)
      usage
      exit
      ;;
    esac
done

build_glclient()
{
  cd ${BUILD_DIR}
  if [ -d ${GLCLIENT_TMP} ]; then
    echo "Directory ${GLBACKEND_TMP} already present and need to be removed"
    read -n1 -p "Do you want to delete ${GLClient_TMP}? (y/n): "
    echo
    if [[ $REPLY != [yY] ]]; then
      echo "Cannot proceed"
      exit
    fi
    rm -rf ${GLCLIENT_TMP} 
  fi
  BUILD_USES_EXISTENT_DIR=0
  if [ -d ${GLCLIENT_DIR} ]; then
    echo "Directory ${GLCLIENT_DIR} already present"
    echo "The build process needs a clean git clone of GLClient"
    echo "If not deleted the build script will use the existent dir"
    read -n1 -p "Do you want to delete ${GLCLIENT_DIR}? (y/n): "
    echo
    if [[ $REPLY == [yY] ]]; then
      echo "Removing directory ${GLCLIENT_DIR}"
      rm -rf ${GLCLIENT_DIR}
    else
      BUILD_USES_EXISTENT_DIR=1
      cp ${GLCLIENT_DIR} ${GLCLIENT_TMP} -r
      cd ${GLCLIENT_TMP}
    fi
  fi
  
  if [ ${BUILD_USES_EXISTENT_DIR} -eq 0 ]; then
    echo "[+] Cloning GLClient in ${GLCLIENT_DIR}"
    git clone $GLCLIENT_GIT_REPO ${GLCLIENT_DIR}
    cp ${GLCLIENT_DIR} ${GLCLIENT_TMP} -r
    cd ${GLCLIENT_TMP}
    if test $TAG; then
      git checkout $TAG
      GLCLIENT_REVISION=$TAG
    else
      GLCLIENT_REVISION=`git rev-parse HEAD | cut -c 1-8`
    fi
  fi

  if [ -f ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz ]; then
    echo "${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz already present"
    exit
  fi

  if [ -f ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip ]; then
    echo "${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip already present"
    exit
  fi

  echo "[+] Building GLClient"
  npm install -d
  grunt build

  mkdir -p ${GLC_BUILD}

  echo "[+] Creating compressed archives"
  mv build glclient-${GLCLIENT_REVISION}
  tar czf ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz glclient-${GLCLIENT_REVISION}/
  md5sum ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz.md5.txt
  sha1sum ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz.sha1.txt
  shasum -a 224 ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.tar.gz.sha224.txt

  zip -r ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip glclient-${GLCLIENT_REVISION}/
  md5sum ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip.md5.txt
  sha1sum ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip.sha1.txt
  shasum -a 224 ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip > ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip.sha224.txt
}
build_glclient
echo "[+] All done!"
echo ""
echo "GLClient build is now present in ${GLC_BUILD}"
echo "GLClient hash: "
cat ${GLC_BUILD}/glclient-${GLCLIENT_REVISION}.zip.sha224.txt
