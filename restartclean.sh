#!/bin/sh

find globaleaks/ -name '*.pyc' -exec rm -f {} \;

./bin/globaleaks --start-clean 1 $@
