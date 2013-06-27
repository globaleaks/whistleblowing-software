#!/bin/bash

if [ ! $GLCLIENT_INSTALL_DIR ];then
  GLCLIENT_INSTALL_DIR=/usr/share/globaleaks/glclient
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
  sudo npm install -g grunt-cli
}

build_custom_glclient()
{
  ( command -v git >/dev/null 2>&1 &&
    command -v node >/dev/null 2>&1 &&
    command -v npm >/dev/null 2>&1 ) || {
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
  TEMPLATE_NAME=$TEMPLATES_DIR
  SED_REGEXP="s/selected_theme = 'default';/selected_theme = '${TEMPLATE_NAME}';/"
  THEMES_FILE=$TMP_DIR/GLCLient/app/scripts/themes.js
  echo "[+] Building custom GLClient with template: ${TEMPLATE_NAME}... "
  cd $TMP_DIR
  echo "[+] Cloning latest GLCLient version... "
  git clone https://github.com/globaleaks/GLClient.git GLCLient
  cat $THEMES_FILE | sed -e $SED_REGEXP > $THEMES_FILE
  cp -R $TEMPLATES_DIR $TMP_DIR/GLCLient/app/templates/${TEMPLATE_NAME}
  cd GLCLient
  npm install -d
  grunt build
  sudo mv $GLCLIENT_INSTALL_DIR $GLCLIENT_INSTALL_DIR.default
  sudo mv build $GLCLIENT_INSTALL_DIR
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
