#!/bin/sh

if [ ! $GLCLIENT_INSTALL_DIR ];then
  GLCLIENT_INSTALL_DIR=/usr/share/globaleaks/glclient
fi

if [ ! $GLCLIENT_TAG ];then
  GLCLIENT_TAG="v"`python -c 'import globaleaks;print globaleaks.__version__'`
fi

usage()
{
cat << EOF
usage: ./build-custom-glclient.sh options

OPTIONS:
    -h                         Show this message
    -r                         Restore to default GLClient installation
    -b <path to templates>     Build custom GLCLient version
    -i                         Install GLClient dependencies
EOF
}

get_sudo()
{
  echo "[+] Let's sudo now, so we don't nag you forever later..."
  command -v sudo >/dev/null 2>&1 || {
    echo "[!] sudo is not installed. No point to continue..."
    exit 2
  }
  sudo echo "Thanks :)"
}

restore_default_glclient()
{
  echo "[+] Restoring to default GLClient... "
  if [ -d $GLCLIENT_INSTALL_DIR.default ];then
    mv $GLCLIENT_INSTALL_DIR.default $GLCLIENT_INSTALL_DIR
    echo "[*] Restored."
  else
    echo "[!] No default installation of GLCLient was found!"
  fi
}

install_glclient_dependencies()
{
  echo "[+] Installing development dependencies... "
  sudo apt-get install git -y
  sudo add-apt-repository ppa:chris-lea/node.js -y
  sudo apt-get update -y
  sudo apt-get install nodejs -y
  sudo npm install -g grunt-cli bower
}

build_custom_glclient()
{
  ( command -v git >/dev/null 2>&1 &&
    command -v node >/dev/null 2>&1 &&
    command -v npm >/dev/null 2>&1 ) || {
    RELEASE="`lsb_release -c|cut -f 2`"
    if [ $RELEASE != "precise" ]; then
      echo "[+] You are not running Ubuntu 12.04 LTS"
      echo "[!] You must install node on your own."
      echo "See: https://github.com/joyent/node/wiki/Installation"
      exit 1
    fi
    echo "[+] Node JS does not appear to be installed."
    while true; do
      read -p "Should we install them? (y|n) " yn
      case $yn in
          [Yy]* ) install_glclient_dependencies; break;;
          [Nn]* ) usage; exit;;
          * ) echo "I only understand yes or no, what do you want from me?";;
      esac
    done
  }

  TMP_DIR=`mktemp -d /tmp/GLClient_tmp.XXXXXXX`
  TEMPLATE_NAME=`basename $TEMPLATES_DIR`
  SED_REGEXP="s/default/${TEMPLATE_NAME}/"
  THEMES_FILE=$TMP_DIR/GLCLient/app/scripts/themes.js
  INDEX_FILE=$TMP_DIR/GLCLient/app/index.html
  STYLES=""
  echo "[+] Building custom GLClient with template: ${TEMPLATE_NAME}... "
  echo "[+] Cloning latest GLCLient version... "
  CWD=`pwd`
  git clone https://github.com/globaleaks/GLClient.git $TMP_DIR/GLCLient
  cd $TMP_DIR/GLCLient
  echo "[+] Checking out ${GLCLIENT_TAG} revision"
  git checkout $GLCLIENT_TAG
  cd $CWD
  cat $THEMES_FILE | sed -e $SED_REGEXP > $TMP_DIR/themes.js
  cat $TMP_DIR/themes.js > $THEMES_FILE
  mkdir $TMP_DIR/staticdata/
  for template_file in `find $TEMPLATES_DIR/styles/ -type f`;do
    if [[ "$template_file" == *css* ]];then
      cat $template_file >> $TMP_DIR/GLCLient/app/styles/custom-glclient.css
    else
      cp $template_file $TMP_DIR/staticdata/
    fi
  done

  if [ -d $TEMPLATES_DIR/images/ ];then
    cp -R $TEMPLATES_DIR/images/ $TMP_DIR/staticdata/
  fi

  cp -R $TEMPLATES_DIR $TMP_DIR/GLCLient/app/templates/${TEMPLATE_NAME}

  cd $TMP_DIR/GLCLient
  npm install -d
  bower update -f
  grunt build

  if [ ! -d  $GLCLIENT_INSTALL_DIR.default ]; then
    echo "[+] Backing up default GLClient build... "
    sudo mv $GLCLIENT_INSTALL_DIR $GLCLIENT_INSTALL_DIR.default
  else
    echo "[+] Cleaning up currently installed custom build... "
    rm -rf $GLCLIENT_INSTALL_DIR
  fi
  sudo mv build $GLCLIENT_INSTALL_DIR
  sudo cp -R $TMP_DIR/staticdata/* $GLCLIENT_INSTALL_DIR
  cd /
  rm -rf $TMP_DIR
}

if [ ! $1 ];then
  usage
fi

while getopts "hrbi:" OPTION
do
  case $OPTION in
    h)
      usage
      exit 1
      ;;
    r)
      restore_default_glclient
      ;;
    b)
      if [ ! $2 ];then
        echo "[!] Missing template directory path."
        usage
        exit 1
      fi

      TEMPLATES_DIR=$2
      get_sudo
      build_custom_glclient
      ;;
    i)
      get_sudo
      install_glclient_dependencies
      ;;
    ?)
      usage
      exit 1
      ;;
  esac
done
