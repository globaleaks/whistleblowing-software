#!/bin/sh

EDITED_FILES="git log \
  --pretty=format: --diff-filter=MA \
  --name-status \
  -1 $TRAVIS_COMMIT \
  --author=vecna"

for file in $($EDITED_FILES | grep '\.py' | cut -f 2); do
    pep8 $file
done
