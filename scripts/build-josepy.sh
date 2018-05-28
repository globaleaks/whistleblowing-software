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

wget http://http.debian.net/debian/pool/main/p/python-josepy/python-josepy_1.0.1.orig.tar.gz
echo '9f48b88ca37f0244238b1cc77723989f7c54f7b90b2eee6294390bacfe870acc  python-josepy_1.0.1.orig.tar.gz' | sha256sum -c
tar zxf python-josepy_1.0.1.orig.tar.gz
wget http://http.debian.net/debian/pool/main/p/python-josepy/python-josepy_1.0.1-1~bpo9+1.debian.tar.xz
echo '0f1c97defc1f3bce7733826a89a67baee27ea5f917ea1f5c5defc813c252d88b  python-josepy_1.0.1-1~bpo9+1.debian.tar.xz' | sha256sum -c
tar xf python-josepy_1.0.1-1~bpo9+1.debian.tar.xz
mv debian josepy-1.0.1
cat >josepy-1.0.1/debian/changelog <<EOL
python-josepy (1.0.1-1) $DISTRIBUTION; urgency=medium

  * GlobaLeaks python-josepy packaging

 -- GlobaLeaks software signing key <info@globaleaks.org>  Mon, 28 May 2018 16:41:13
EOL

cat >josepy-1.0.1/debian/rules <<EOL
#!/usr/bin/make -f

export PYBUILT_NAME = josepy

%:
	dh $@ --with python2,python3 --buildsystem=pybuild
EOL
