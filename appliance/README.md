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


### Example for Ubuntu 14.04 for running the latest release

On your local machine:

```bash
> cd templates/ubuntu-14.04
> packer build template.json
```


### Example for Ubuntu 16.04 for running a development package

```bash
# Create the globaleaks debian package you intend to install
> ./scripts/build.sh -t devel -d xenial -n
> cp /path/to/globaleaks_2.64.11_all.deb data/
> cd templates/ubuntu-16.04
> packer build templates/ubuntu-16.04/template.json
```

### Commands for running the VM
```bash
> vagrant init
> vagrant up
> curl 127.0.0.1:8082
