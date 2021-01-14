Release Procedure
=================
# Release procedure

This is the procedure followed to release a new GlobaLeaks release

Changelog and Tag the Release
-----------------------------
A release is represented by:

* A version bump on files: backend/globaleaks/__init__.py, client/packages.json, client/npm-shrinkwrap.json
* An updated changelog in: CHANGELOG and debian/changelog
* A commit "Bump to verson $number"
* A tag commit $version signed by a core developer with its own key

The tag commit is is issued via:
.. code:: sh

  export DEBFULLNAME="GlobaLeaks software signing key"
  export DEBEMAIL="info@globaleaks.org"
  dch -i
  git commit -a -m "commit before new tag message"
  git push origin
  git tag -s v0.1 -m 'GlobaLeaks version 0.1'
  git push origin --tags

Build the Release
-----------------
The release is built by means of the official official build script by issuing:

.. code:: sh

  cd GlobaLeaks && ./script/build -d all

This command builds a package for each supported distribution and version.

Publishing of the Release
-------------------------
The package is published on deb.globalekas.org by issuing:

.. code:: sh

  dput globaleaks ../globaleaks_${version}_all.changes

Signing of the Release
----------------------
The release is then signed by a core developer by using the official project key via:
  gpg --detach-sign --digest-algo SHA512 -o Release.gpg Release
