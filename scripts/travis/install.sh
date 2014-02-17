#!/bin/sh

set -e

wget https://raw.github.com/globaleaks/GLBackend/master/requirements.txt -O /tmp/requirements.txt
pip install -r /tmp/requirements.txt
