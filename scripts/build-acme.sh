#!/bin/bash
set -e

DISTRIBUTION=xenial

while getopts "d:" opt; do
  case $opt in
    d) DISTRIBUTION="$OPTARG"
    ;;
    \?) usage
        exit 1
    ;;
  esac
done

wget http://http.debian.net/debian/pool/main/p/python-acme/python-acme_0.22.2.orig.tar.gz
echo '0ecd0ea369f53d5bc744d6e72717f9af2e1ceb558d109dbd433148851027adb4  python-acme_0.22.2.orig.tar.gz' | sha256sum -c
tar zxf python-acme_0.22.2.orig.tar.gz
wget http://http.debian.net/debian/pool/main/p/python-acme/python-acme_0.22.2-1~bpo9+1.debian.tar.xz
echo '0c7fc3d015cec33de4bc762deea53cdbf191838e9b849ebbd3a0432c135dd7d1' python-acme_0.22.2-1~bpo9+1.debian.tar.xz | sha256sum -c
tar xf python-acme_0.22.2-1~bpo9+1.debian.tar.xz
mv debian acme-0.22.2

cat >acme-0.22.2/debian/changelog <<EOL
python-acme (0.22.2-1) $DISTRIBUTION; urgency=medium

  * GlobaLeaks python-acme packaging

 -- GlobaLeaks software signing key <info@globaleaks.org>  Mon, 28 May 2018 16:41:13
EOL
