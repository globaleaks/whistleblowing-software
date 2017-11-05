#!/bin/bash -e
echo "**** Starting GlobaLeaks ..."
service tor start
/usr/src/globaleaks/backend/bin/globaleaks --allow-run-as-root -n
