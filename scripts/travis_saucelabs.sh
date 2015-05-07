#!/bin/bash

declare -a capabilities=(
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"Linux\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"firefox\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"Linux\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"chrome\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"safari\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"iphone\", \"version\":\"8.2\", \"platform\":\"OS X 10.10\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"8\", \"platform\":\"Windows 7\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"9\", \"platform\":\"Windows 7\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"10\", \"platform\":\"Windows 8\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"version\":\"11\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"platform\":\"Windows 8.1\"}'"
  "export SELENIUM_BROWSER_CAPABILITIES='{\"browserName\":\"internet explorer\", \"platform\":\"Windows 8.1\"}'"
)

## now loop through the above array
for i in "${capabilities[@]}"
do
   eval $i
   $TRAVIS_BUILD_DIR/backend/bin/globaleaks -z travis -c -k9
   sleep 5
   grunt protractor:saucelabs
done
