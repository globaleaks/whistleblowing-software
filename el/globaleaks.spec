%global commit      5762d913f9b80a4f30d41cc0ee9b1ee41242b500
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global version     4.0.58

%define debug_package %{nil}
%define _unpackaged_files_terminate_build 0

Name: globaleaks
Version: %{version}
Release: 1.%{shortcommit}%{?dist}
Summary: Opensource whistleblowing platform.
License: see /usr/share/doc/globaleaks/copyright
Group: Converted/web
ExclusiveArch: x86_64

URL:            https://globaleaks.org
Source0:        https://github.com/globaleaks/GlobaLeaks/archive/%{commit}.tar.gz
Source1:	globaleaks.service

BuildRequires: nodejs
BuildRequires: python36

Requires: python3-twisted
Requires: python3-priority
Requires: python3-h2
Requires: python3-sqlalchemy
Requires: python3-pynacl
Requires: python3-gnupg
Requires: python3-josepy
Requires: python3-acme
Requires: python3-pyotp
Requires: python-txtorcon

Requires: tor
Requires: haveged

%prep
%setup -n GlobaLeaks-%{commit}

%build

# Build Client
cd client
npm install -d
./node_modules/grunt/bin/grunt build
cd ../

# Build Backend
cd backend
python3 setup.py build
cd ../

%install

# Install Backend
cd backend
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
cd ../

# Configure
sed -i "s|^WORKING_DIR.*|WORKING_DIR=/var/lib/globaleaks/|" backend/default
sed -i "s|^APPARMOR_SANDBOXING.*|APPARMOR_SANDBOXING=0|" backend/default

# Change ports to unprivileges ports
sed -i 's|http://%s|http://%s:8080|g' $RPM_BUILD_ROOT/usr/lib/python3.6/site-packages/globaleaks/backend.py
sed -i 's|https://%s|https://%s:4443|g' $RPM_BUILD_ROOT/usr/lib/python3.6/site-packages/globaleaks/backend.py
sed -i 's|80, 443|8080, 4443|g' $RPM_BUILD_ROOT/usr/lib/python3.6/site-packages/globaleaks/settings.py
sed -i 's|port == 80|port == 8080|g' $RPM_BUILD_ROOT/usr/lib/python3.6/site-packages/globaleaks/backend.py
sed -i 's|port == 443|port == 4443|g' $RPM_BUILD_ROOT/usr/lib/python3.6/site-packages/globaleaks/backend.py

# Install Rest
mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
cp %{_sourcedir}/globaleaks.service $RPM_BUILD_ROOT/usr/lib/systemd/system/
mkdir -p $RPM_BUILD_ROOT/usr/share/globaleaks/client
cp LICENSE $RPM_BUILD_ROOT/usr/share/globaleaks/LICENSE
cp CHANGELOG $RPM_BUILD_ROOT/usr/share/globaleaks/CHANGELOG
cp backend/default $RPM_BUILD_ROOT/usr/share/globaleaks/default
cp -ar client/build/* $RPM_BUILD_ROOT/usr/share/globaleaks/client
mkdir -p $RPM_BUILD_ROOT/var/lib/globaleaks

%pre
#!/bin/sh
# This is the post installation script for globaleaks
set -e



if [ "$1" = "upgrade" ]; then
  systemctl stop globaleaks || true
fi

if [ ! -z "$(ls -A /var/globaleaks 2>/dev/null)" ]; then
  if ! id -u globaleaks >/dev/null 2>&1; then
    adduser --system \
            --home /var/globaleaks \
            --shell /bin/false \
            globaleaks
  fi
fi


%post
#!/bin/sh
# This is the post installation script for globaleaks
set -e

# Create globaleaks user and add the user to required groups
if ! id -u globaleaks >/dev/null 2>&1; then
  adduser --system \
          --home /var/globaleaks \
          --shell /bin/false \
          globaleaks
fi

usermod -a -G toranon globaleaks

# Create globaleaks service directories with proper permissios
gl-fix-permissions

# Remove old configuration of Tor used before txtorcon adoption
if $(grep -q -i globaleaks /etc/tor/torrc >/dev/null 2>&1); then
  sed -i '/BEGIN GlobaLeaks/,/END GlobaLeaks/d' /etc/tor/torrc
  systemctl enable tor
  systemctl restart tor
fi

# raise haveged default water mark to 4067 bits
# for the reason for the 4067 bits see:
#   - https://github.icom/globaleaks/GlobaLeaks/issues/1722
cp /usr/lib/systemd/system/haveged.service /etc/systemd/system/haveged.service
sed -i 's/-w 1024/-w 4067/g' /etc/systemd/system/haveged.service
systemctl enable tor
systemctl restart haveged

systemctl enable globaleaks
systemctl restart globaleaks

%preun
#!/bin/sh
set -e

systemctl stop globaleaks

%description
GlobaLeaks is an open source project aimed to create a worldwide, anonymous,
censorship-resistant, distributed whistleblowing platform.

%files
%defattr(0644, globaleaks, globaleaks, 0755)
/usr/bin/gl-admin
/usr/bin/gl-fix-permissions
/usr/bin/globaleaks
/usr/lib/python3.6/site-packages/globaleaks/
/usr/lib/python3.6/site-packages/globaleaks-4.0.58-py3.6.egg-info/
/usr/share/globaleaks/
/usr/lib/systemd/system/globaleaks.service
%attr(0755, globaleaks, globaleaks) /var/lib/globaleaks
