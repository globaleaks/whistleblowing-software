# GlobaLeaks Appliance Scripts

The aim of this folder is to keep track of a plethora of GlobaLeaks Applicance
solutions.

The solutions currently taken into consideration are the following:

* [Packer](https://github.com/globaleaks/GLAppliance/tree/master/Packer)
* [Vagrant](https://github.com/globaleaks/GLAppliance/tree/master/Vagrant)
* [Docker](https://github.com/globaleaks/GLAppliance/tree/master/Docker)

Thanks to one of the above solutions it is possible to:

* Easily instantiate GlobaLeaks Demos;
* Perform Manual and Automatic Unit Testing;
* Easily instatiate a Full Fladged GlobaLeaks Appliance.


## GlobaLeaks Packer Script

[Packer](https://www.packer.io/) is a tool for building identical machine images
for multiple platforms from a single source configuration.

This can be used for example in order to:

* automatically build GlobaLeaks VirtualBox images;
* automatically build Globaleaks VMware Images;
* deploy GlobaLeaks on Cloud Services (AMIs EC2, ..)!
* test GlobaLeaks for new deployments

### End2End installation testing of GlobaLeaks

The appliance workflow here is designed to emulate the intended installation behaivor of GlobaLeaks on supported platforms.

The idea is to automate the installation, enabling continious testing and quick deployments of the application

Supported methods:
- Ubuntu 14.04 : via wget of installation script
Planned methods:
- Ubuntu 16.04 : via debian package
- CentOS 6 : via ???


### Ubuntu 14.04
On your local machine:

```bash
> /path/to/packer build templates/ubuntu-14.04/template.json
> vagrant init
# Name box, edit Vagrant file add ip=191.168.33.10
> vagrant up
# Check everything is working 
> curl 191.168.33.10:8082
# Run E2E tests with something like:
> ./node_modules/protractor/bin/protractor --baseUrl http://191.168.33.10:8082 tests/end2end/protractor-coverage.config.js
```

