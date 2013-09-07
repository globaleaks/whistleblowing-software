# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "precise32"
  config.vm.box_url = "http://files.vagrantup.com/precise32.box"
  config.vm.network :forwarded_port, guest: 8082, host: 8082
end

$script = <<SCRIPT

# 1 - Install Tor
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-1---install-tor

apt-get update
apt-get -y install python-software-properties
add-apt-repository 'deb http://deb.torproject.org/torproject.org precise main'
gpg --keyserver x-hkp://pool.sks-keyservers.net --recv-keys 0x886DDD89
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -
apt-get update
apt-get -y install tor tor-geoipdb curl

# 2 - Install GlobaLeaks
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-2---install-globaleaks

curl https://raw.github.com/globaleaks/GlobaLeaks/master/scripts/install-ubuntu-12_04.sh > install-ubuntu-12_04.sh
chmod +x install-ubuntu-12_04.sh
./install-ubuntu-12_04.sh -y

# 3 - Configure Tor
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-3---configure-tor

echo "VirtualAddrNetwork 10.23.47.0/10" >> /etc/tor/torrc
echo "AutomapHostsOnResolve 1" >> /etc/tor/torrc
echo "TransPort 9040" >> /etc/tor/torrc
echo "TransListenAddress 127.0.0.1" >> /etc/tor/torrc
echo "DNSPort 5353" >> /etc/tor/torrc
echo "DNSListenAddress 127.0.0.1" >> /etc/tor/torrc

# 4 - Create your Tor Hidden Service
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-4---create-your-hidden-service

echo "HiddenServiceDir /var/globaleaks/torhs/" >> /etc/tor/torrc
echo "HiddenServicePort 80 127.0.0.1:8082" >> /etc/tor/torrc

/etc/init.d/apparmor restart
/etc/init.d/tor restart

# 5 - Start GlobaLeaks 
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-5---start-globaleaks 

/etc/init.d/globaleaks start

# 6 - Configure GlobaLeaks
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-6---configure-globaleaks

echo "##########"
echo "# GlobaLeaks is running with this Tor Hidden Service address:"
echo -n "# "
cat /var/globaleaks/torhs/hostname
echo "##########"

# 7 - Setup GlobaLeaks to run automatically
# https://github.com/globaleaks/GlobaLeaks/wiki/Installation-guide#step-7---setup-globaleaks-to-run-automatically

update-rc.d globaleaks defaults

# XXX
# We need to add the local vagrant interface IP address to the list of allowed hosts inside of /etc/default/globaleaks

SCRIPT

Vagrant.configure("2") do |config|
  config.vm.provision :shell, :inline => $script
end
