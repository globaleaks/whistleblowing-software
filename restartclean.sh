#!/bin/sh

# remove database and submission files
rm -rf _gldata

find globaleaks/ -name '*.pyc' -exec rm -f {} \;

./bin/startglobaleaks
