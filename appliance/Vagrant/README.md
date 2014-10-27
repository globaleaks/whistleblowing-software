# GlobaLeaks Vagrant Script

[Vagrant](http://www.vagrantup.com/) is an tool for managing virtual machines via a simple to use command line interface.

With a simple “vagrant up” you can be working in a clean GlobaLeaks environment.

By means of “provisioners” in Vagrant it's possible to automatically install the GlobaLeaks software, alter its configurations, and more!

This can be used for example in order to:

* Automatize GlobaLeaks Unit Testing
* Automatize GlobaLeaks setup Process

The images that [Packer](https://github.com/globaleaks/GLAppliance/Packer) creates can easily be turned into Vagrant boxes.
