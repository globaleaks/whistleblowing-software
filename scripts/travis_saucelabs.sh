#!/bin/bash

declare -a capabilities=(
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"Linux\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"36.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"version\":\"37.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"Linux\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"37.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"38.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"39.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"40.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"41.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"version\":\"42.0\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 8.1\"}'"
)

## now loop through the above array
for i in "${capabilities[@]}"
do
   eval $i
   $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9 --port 8080
   sleep 5
   grunt protractor:saucelabs
done
