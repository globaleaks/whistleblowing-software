#!/bin/bash
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

AUTOYES=0
while getopts “yhv:” OPTION
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
      AUTOYES=1
      ;;
    ?)
      usage
      exit
      ;;
    esac
done

auto_env_setup()
{
  cd ${BUILD_DIR}
  if [ -d ${GLCLIENT_TMP} ]; then
    echo "[+] detected and removing ${GLCLIENT_TMP}"
    rm -rf ${GLCLIENT_TMP} 
  fi
  if [ -d ${GLCLIENT_DIR} ]; then
    echo "[+] detected source repository in ${GLCLIENT_DIR}"
    cp ${GLCLIENT_DIR} ${GLCLIENT_TMP} -r
    USING_EXISTENT_DIR=1
  else
    echo "[+] Cloning GLClient in ${GLCLIENT_TMP}"
    git clone $GLCLIENT_GIT_REPO ${GLCLIENT_TMP}
  fi
}

interactive_env_setup()
{
  cd ${BUILD_DIR}
  if [ -d ${GLCLIENT_TMP} ]; then
    echo "Directory ${GLCLIENT_TMP} already present and need to be removed"
    ANSWER=''
    until [[ $ANSWER = [yn] ]]; do
      read -n1 -p "Do you want to delete ${GLCLIENT_TMP}? (y/n): " ANSWER
      echo
    done
    if [[ $ANSWER != 'y' ]]; then
      echo "Cannot proceed"
      exit
    fi
    rm -rf ${GLCLIENT_TMP} 
  fi
  if [ -d ${GLCLIENT_DIR} ]; then
    echo "Directory ${GLCLIENT_DIR} already present. "
    ANSWER=''
    until [[ $ANSWER = [yn] ]]; do
      read -n1 -p "Do you want to use the existent ${GLCLIENT_DIR}? (y/n): " ANSWER
      echo
    done
    if [[ $ANSWER != 'y' ]]; then
      echo "[+] Cloning GLClient in ${GLCLIENT_TMP}"
      git clone $GLCLIENT_GIT_REPO ${GLCLIENT_TMP}
    else
      echo "[+] Copying existent ${GLCLIENT_DIR} in ${GLCLIENT_TMP}"
      cp ${GLCLIENT_DIR} ${GLCLIENT_TMP} -r
      USING_EXISTENT_DIR=1
    fi
  else
    echo "[+] Cloning GLClient in ${GLCLIENT_TMP}"
    git clone $GLCLIENT_GIT_REPO ${GLCLIENT_TMP}
  fi
}

build_glclient()
{
  cd ${GLCLIENT_TMP}

  if test ${USING_EXISTENT_DIR}; then
    echo "Using GLClient existent directory and respective HEAD"
  else
    if test $TAG; then
      echo "Using a clean cloned GLClient directory"
      echo "Checking out $TAG (if existent, using master HEAD instead)"
      git checkout $TAG >& /dev/null || git checkout HEAD >& /dev/null
    fi
  fi

  GLCLIENT_REVISION=`git rev-parse HEAD | cut -c 1-8`

  echo "Revision used: ${GLCLIENT_REVISION}"

  if not test $TAG; then
    TAG=${GLCLIENT_REVISION}
  fi

  if [ -f ${GLC_BUILD}/glclient-${TAG}.tar.gz ]; then
    echo "${GLC_BUILD}/glclient-${TAG}.tar.gz already present"
    exit
  fi

  if [ -f ${GLC_BUILD}/glclient-${TAG}.zip ]; then
    echo "${GLC_BUILD}/glclient-${TAG}.zip already present"
    exit
  fi

  echo "[+] Building GLClient"
  npm install -d
  grunt build

  mkdir -p ${GLC_BUILD}

  echo "[+] Creating compressed archives"
  mv build glclient-${TAG}
  tar czf ${GLC_BUILD}/glclient-${TAG}.tar.gz glclient-${TAG}/
  md5sum ${GLC_BUILD}/glclient-${TAG}.tar.gz > ${GLC_BUILD}/glclient-${TAG}.tar.gz.md5.txt
  sha1sum ${GLC_BUILD}/glclient-${TAG}.tar.gz > ${GLC_BUILD}/glclient-${TAG}.tar.gz.sha1.txt
  shasum -a 224 ${GLC_BUILD}/glclient-${TAG}.tar.gz > ${GLC_BUILD}/glclient-${TAG}.tar.gz.sha224.txt

  zip -r ${GLC_BUILD}/glclient-${TAG}.zip glclient-${TAG}/
  md5sum ${GLC_BUILD}/glclient-${TAG}.zip > ${GLC_BUILD}/glclient-${TAG}.zip.md5.txt
  sha1sum ${GLC_BUILD}/glclient-${TAG}.zip > ${GLC_BUILD}/glclient-${TAG}.zip.sha1.txt
  shasum -a 224 ${GLC_BUILD}/glclient-${TAG}.zip > ${GLC_BUILD}/glclient-${TAG}.zip.sha224.txt
}

if [ $AUTOYES -eq 1 ]; then
  auto_env_setup
else
  interactive_env_setup
fi
build_glclient

echo "[+] All done!"
echo ""
echo "GLClient build is now present in ${GLC_BUILD}"
echo "GLClient hash: "
cat ${GLC_BUILD}/glclient-${TAG}.zip.sha224.txt
