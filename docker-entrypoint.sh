#!/bin/bash -e
echo "**** Starting GlobaLeaks ..."
service tor start
exec /usr/src/globaleaks/backend/bin/globaleaks --allow-run-as-root -n
