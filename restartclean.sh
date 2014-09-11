#!/bin/sh

find globaleaks/ -name '*.pyc' -delete

./bin/globaleaks --start-clean 1 $@
