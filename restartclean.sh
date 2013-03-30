#!/bin/sh

find globaleaks/ -name '*.pyc' -exec rm -f {} \;

./bin/startglobaleaks --start-clean 1
