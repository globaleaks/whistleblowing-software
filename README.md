# Quickstart

Greetings!

Getting started with hacking on GLClient is easier than you may think, it's
just a matter of having the right dependencies.

You should first install a version of node.js that includes the node package
manager npm.

Check out:
https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager for
details on installing node.js with the OS flavour of your choice.

On ubuntu 12.10, for example, you will do
(https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#ubuntu):

    sudo add-apt-repository ppa:chris-lea/node.js
    apt-get install nodejs npm git
    sudo apt-get update
    sudo apt-get install nodejs

## Install node depedencies

First install grunt-cli globally:

    sudo npm install -g grunt-cli

Then you shall install the development dependencies:

    npm install -d

At this point you will be able to build the compacted version of GLClient with:

    grunt build

This will create a directory called `build` where you will inside find:

    build/images/
    build/index.html
    build/scripts.js
    build/styles.css

For more information see below.

## More documentation

  * [Main GlobaLeaks documentation](https://github.com/globaleaks/GlobaLeaks/wiki/Home)
  * [GLClient specific documentation](https://github.com/globaleaks/GLClient/wiki/Home)
