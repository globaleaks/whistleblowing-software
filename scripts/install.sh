#!/bin/bash

############## Start Of Variable and Functions Declaration ###########

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR=/tmp/glbuilding.$RANDOM
BUILD_LOG=${BUILD_DIR}.log
TMP_KEYRING=${BUILD_DIR}/tmpkeyring.gpg
DISTRO='unknown'
DISTRO_VERSION='unknown'

if [ -f /etc/redhat-release ]; then
  DISTRO="fedora"
# Debian/Ubuntu
elif [ -r /lib/lsb/init-functions ]; then
  if [ "$( lsb_release -is )" == "Debian" ]; then
    DISTRO="debian"
    DISTRO_VERSION="$( lsb_release -cs )"
  else
    DISTRO="ubuntu"
    DISTRO_VERSION="$( lsb_release -cs )"
  fi
fi

echo "Performing installation on $DISTRO - $DISTRO_VERSION"

if [ $DISTRO != 'ubuntu' ]; then
  echo "!!!!!!!!!!!! WARNING !!!!!!!!!!!!"
  echo "You are attempting to install GlobaLeaks on an unsupported platform."
  echo "Do you wish to continue at your own risk [Y|N]? "
  read ans
  if [ $ans = y -o $ans = Y -o $ans = yes -o $ans = Yes -o $ans = YES ]
  then
    echo "Ok, you wanted it!"
  else
    echo "Ok, no worries. Still friends, right?"
    exit
  fi
fi

usage()
{
cat << EOF
usage: ./${SCRIPTNAME} options

OPTIONS:
   -h      Show this message
   -y      To assume yes to all queries

EOF
}

ASSUME_YES=0
while getopts “hv:ny” OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
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

DO () {
    if [ -z "$2" ]; then
        RET=0
    else
        RET=$2
    fi
    if [ -z "$3" ]; then
        CMD=$1
    else
        CMD=$3
    fi
    echo -n "Running: \"$CMD\"... "
    $1 &>${BUILD_LOG}
    if [ "$?" -eq "$2" ]; then
        echo "SUCCESS"
    else
        echo "FAIL"
        echo "COMBINED STDOUT/STDERR OUTPUT OF FAILED COMMAND:"
        cat ${BUILD_LOG}
        exit 1
    fi
}

add_repository () {
  # Distro independent function for adding a line to apt sources.list
  REPO="$(echo $1 | sed 's/DISTRO_VERSION/${DISTRO_VERSION}/')"
  if which add-apt-repository >/dev/null 2>&1;then
    add-apt-repository -y "$REPO"
  else
    if grep -Fxq "$REPO" /etc/apt/sources.list
    then
      echo "Repository already present. Not adding it..."
    else
      echo $REPO >> /etc/apt/sources.list
    fi
  fi
}

vercomp () {
    # Returnned values:
    #   0: version are equals
    #   1: $1 is bigger than $2
    #   2: $2 is bigger than $1
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}

GLOBALEAKS_KEY_FILE=${BUILD_DIR}/gl-pub-key.gpg
GLOBALEAKS_PUB_KEY="
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.12 (GNU/Linux)

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
=3NLy
-----END PGP PUBLIC KEY BLOCK-----
"

NEEDED_VERSION_PYTHON=2.7
NEEDED_VERSION_PIP=1.3.1

PIP_PKG="pip-${NEEDED_VERSION_PIP}.tar.gz"
PKG_VERIFY=${BUILD_DIR}/${PIP_PKG}.asc
PIP_URL="https://pypi.python.org/packages/source/p/pip/${PIP_PKG}"
PIP_SIG_URL="https://pypi.python.org/packages/source/p/pip/${PIP_PKG}.asc"
PIP_KEY_FILE=${BUILD_DIR}/pip-pub-key.gpg
PIP_PUB_KEY="
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.12 (Darwin)
Comment: GPGTools - http://gpgtools.org

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
=0zqq
-----END PGP PUBLIC KEY BLOCK-----
"

############### End Of Variable and Functions Declaration ############

# User Permission Check
if [[ "$EUID" -ne "0" ]]; then
    echo "Error: GlobaLeaks install script must be runned by root"
    exit 1
fi

mkdir -p ${BUILD_DIR}
chmod 700 ${BUILD_DIR}
cd ${BUILD_DIR}

# iptables NAT support check
if [ "${TRAVIS}" == "true" ]; then
    echo "Travis Environment: skipping iptables NAT check support"
else
    iptables -nvL -t nat >/dev/null 2>&1
    if [ "$?" -ne "0" ]; then
        echo "Error: your linux machine does not support iptables NAT, required by GlobaLeaks network sandboxing"
        echo "       If you are running on a Virtual Server you need to enable Iptables NAT support"
        exit 1
    fi
fi

# Preliminary Requirements Check
REQS=(apt-get chmod echo gpg python mkdir tar wget)
REQS_COUNT=${#REQS[@]}
ERR=0
echo "Checking preliminary GlobaLeaks requirements"
for ((i=0;i<REQS_COUNT;i++)); do
    if which ${REQS[i]} >/dev/null; then
        echo " + ${REQS[i]} requirements meet"
    else
        ERR=$[ERR+1]
        echo " - ${REQS[i]} requirement not meet"
    fi
done

if [ $ERR -ne 0 ]; then
    echo "Error: Found ${ERR} unmet requirements"
    exit 1
fi

INSTALLED_PYTHON=`python --version 2>&1 | cut -d" " -f2`
vercomp ${INSTALLED_PYTHON} ${NEEDED_VERSION_PYTHON}
if [ "$?" -eq "2" ]; then
    echo "Error: Globaleaks needs at least python version ${NEEDED_VERSION_PYTHON} (found ${INSTALLED_PYTHON})"
    exit 1
fi

DO "apt-get update -y" "0"

DO "locale-gen en_US.UTF-8" "0"

if [ $DISTRO_VERSION != 'trusty' ]; then
    echo "Installing python-software-properties"
    DO "apt-get install python-software-properties -y" "0"
fi

if [ $DISTRO == 'ubuntu' ];then
  echo "Adding Ubuntu Universe repository"
  add_repository "deb http://de.archive.ubuntu.com/ubuntu/ $DISTRO_VERSION universe"
  DO "apt-get update -y" "0"
fi

echo "Installing gcc, python-setuptools, python-dev, libffi-dev, libssl-dev"
DO "apt-get install gcc python-setuptools python-dev libffi-dev libssl-dev -y" "0"

echo "${GLOBALEAKS_PUB_KEY}" > ${GLOBALEAKS_KEY_FILE}
DO "gpg --no-default-keyring --keyring ${TMP_KEYRING} --import ${GLOBALEAKS_KEY_FILE}" "0"

INSTALL_PIP=1
if which pip >/dev/null 2>&1; then
    INSTALLED_PIP=`pip --version | cut -d" " -f2`
    vercomp ${INSTALLED_PIP} ${NEEDED_VERSION_PIP}
    if [ "$?" -ne "2" ]; then
        INSTALL_PIP=0
    fi
fi

if [ "${INSTALL_PIP}" -eq "1" ] ; then
  DO "wget -O ${BUILD_DIR}/${PIP_PKG} ${PIP_URL}" "0"
  DO "wget -O ${BUILD_DIR}/${PIP_PKG}.asc ${PIP_SIG_URL}" "0"

  echo "Verifying PGP signature"
  echo "${PIP_PUB_KEY}" > ${PIP_KEY_FILE}
  DO "gpg --no-default-keyring --keyring $TMP_KEYRING --import $PIP_KEY_FILE" "0"
  DO "gpg --no-default-keyring --keyring $TMP_KEYRING --verify $PKG_VERIFY" "0"

  DO "tar xzf ${BUILD_DIR}/${PIP_PKG}" "0"
  DO "cd pip-*" "0"

  echo "Installing the latest pip"
  if [ "${ASSUME_YES}" -eq "0" ]; then
    echo "WARNING this will overwrite the pip that you currently have installed and all python dependencies will be installed via pip."
    ANSWER=''
    until [[ $ANSWER = [yn] ]]; do
      read -r -p "Do you wish to continue? [y/n]" ANSWER
      echo
    done
    if [[ $ANSWER != 'y' ]]; then
      echo "Cannot proceed"
      exit
    fi
  fi
  DO "python setup.py install" "0"
fi

if [ -f ${DIR}/../../GLBackend_tmp/requirements.txt ]; then
  PIP_DEPS=`cat ${DIR}/../../GLBackend_tmp/requirements.txt`
else
  DO "wget -O ${BUILD_DIR}/requirements.txt https://raw.github.com/globaleaks/GLBackend/master/requirements.txt" "0"
  PIP_DEPS=`cat ${BUILD_DIR}/requirements.txt`
fi

for PIP_DEP in ${PIP_DEPS}; do
  DO "pip install ${PIP_DEP}" "0"
done

if [ -d /data/globaleaks/deb ]; then
  echo "Installing Deb package from local dir /data/globaleaks/deb"
  cd /data/globaleaks/deb/ && dpkg-scanpackages . /dev/null | gzip -c -9 > /data/globaleaks/deb/Packages.gz
  if [ ! "`grep "deb file:///data/globaleaks/deb/ /" /etc/apt/sources.list`" ]; then
    echo 'deb file:///data/globaleaks/deb/ /' >> /etc/apt/sources.list
  fi
  DO "apt-get update -y" "0"
  DO "apt-get install globaleaks -y --force-yes -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confnew" "0"
else
  echo "Fetching Deb package from remote repository http://deb.globaleaks.org/"
  add_repository 'deb http://deb.globaleaks.org/ unstable/'
  DO "gpg --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 0x24045008" "0"
  # TODO: This should be fixed, because executing this command
  # over DO() command escape the pipe character
  gpg --export B353922AE4457748559E777832E6792624045008 | apt-key add -
  DO "apt-get update -y" "0"
  DO "apt-get install globaleaks -y" "0"
fi
