#!/bin/sh

find globaleaks/ -name '*.pyc' -exec rm -f {} \;

./bin/startglobaleaks --restart-clean 1
