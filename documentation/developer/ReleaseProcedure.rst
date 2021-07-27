=================
Release Procedure
=================
This is the procedure followed to publish a new GlobaLeaks release.

A release is represented by:

* A version bump;
* An updated CHANGELOG;
* A commit titled "Bump to version $number";
* A tag commit $version signed by a core developer with its own key;
* An updated package on deb.globaleaks.org;
* A signed repository.

Release Tagging
===============
The release is represented by a tag commit on Github performed via:

.. code:: sh

  export DEBFULLNAME="GlobaLeaks software signing key"
  export DEBEMAIL="info@globaleaks.org"
  dch -i
  git commit -a -m "commit before new tag message"
  git push origin
  git tag -s v0.1 -m 'GlobaLeaks version 0.1'
  git push origin --tags

Release Packaging
=================
The package is built by means of the official official build script by issuing:

.. code:: sh

  cd GlobaLeaks && ./script/build -d all

This command builds a package for each supported distribution and version.

Package Publishing
==================
The package is published on deb.globalekas.org by issuing:

.. code:: sh

  dput globaleaks ../globaleaks_${version}_all.changes

Repository Signing
==================
The release is then signed by a core developer by using the official project key via:

.. code:: sh

  gpg --detach-sign --digest-algo SHA512 -o Release.gpg Release
