Release Checklist
=================

* ensure local copy is on master, up-to-date:
   * git checkout master
   * git pull

* double-check version updated, sadly in a few places:
   * Makefile
   * txtorcon/_metadata.py

* run all tests, on all configurations
   * "detox"

* ensure long_description will render properly:
   * python setup.py check -r -s
   * tox -e readme_render

* "make pep8" should run cleanly (ideally)

* update docs/releases.rst to reflect upcoming reality
   * blindly make links to the signatures
   * update heading, date

* on both signing-machine and build-machine shells:
   * export VERSION=18.0.0

* (if on signing machine) "make dist" and "make dist-sigs"
   * creates:
     dist/txtorcon-${VERSION}.tar.gz.asc
     dist/txtorcon-${VERSION}-py2.py3-none-any.whl.asc
   * add the signatures to "signatues/"
     cp dist/txtorcon-${VERSION}.tar.gz.asc dist/txtorcon-${VERSION}-py2.py3-none-any.whl.asc signatures/
   * add ALL FOUR files to dist/ (OR fix twine commands)

* (if not on signing machine) do "make dist"
  * scp dist/txtorcon-${VERSION}.tar.gz dist/txtorcon-${VERSION}-py2-none-any.whl signingmachine:
  * sign both, with .asc detached signatures
     * gpg --no-version --detach-sign --armor --local-user meejah@meejah.ca txtorcon-${VERSION}-py2-none-any.whl
     * gpg --no-version --detach-sign --armor --local-user meejah@meejah.ca txtorcon-${VERSION}.tar.gz
  * copy signatures back to build machine, in dist/
  * double-check that they validate::
     gpg --verify dist/txtorcon-${VERSION}-py2.py3-none-any.whl.asc
     gpg --verify dist/txtorcon-${VERSION}.tar.gz.asc

* generate sha256sum for each::
     sha256sum dist/txtorcon-${VERSION}.tar.gz dist/txtorcon-${VERSION}-py2.py3-none-any.whl

* copy signature files to <root of dist>/signatures and commit them
  along with the above changes for versions, etc.

* draft email to tor-dev (and probably twisted-python):
   * example: https://lists.torproject.org/pipermail/tor-dev/2014-January/006111.html
   * example: https://lists.torproject.org/pipermail/tor-dev/2014-June/007006.html
   * copy-paste release notes, un-rst-format them
   * include above sha256sums
   * clear-sign the announcement
   * gpg --armor --clearsign -u meejah@meejah.ca release-announce-${VERSION}
   * Example boilerplate:

           I'm [adjective] to announce txtorcon 0.10.0. This adds
           several amazing features, including levitation. Full list
           of improvements:

              * take from releases.rst
              * ...but un-rST them

           You can download the release from PyPI or GitHub (or of
           course "pip install txtorcon"):

              https://pypi.python.org/pypi/txtorcon/0.10.0
              https://github.com/meejah/txtorcon/releases/tag/v0.10.0

           Releases are also available from the hidden service:

              http://timaq4ygg2iegci7.onion/txtorcon-0.12.0.tar.gz
              http://timaq4ygg2iegci7.onion/txtorcon-0.12.0.tar.gz.asc

           Or via a "version 3" service:

              http://fjblvrw2jrxnhtg67qpbzi45r7ofojaoo3orzykesly2j3c2m3htapid.onion/txtorcon-18.0.0.tar.gz
              http://fjblvrw2jrxnhtg67qpbzi45r7ofojaoo3orzykesly2j3c2m3htapid.onion/txtorcon-18.0.0.tar.gz.asc

           You can verify the sha256sum of both by running the following 4 lines
           in a shell wherever you have the files downloaded:

           cat <<EOF | sha256sum --check
           910ff3216035de0a779cfc167c0545266ff1f26687b163fc4655f298aca52d74  txtorcon-0.10.0-py2-none-any.whl
           c93f3d0f21d53c6b4c1521fc8d9dc2c9aff4a9f60497becea207d1738fa78279  txtorcon-0.10.0.tar.gz
           EOF

           thanks,
           meejah

* copy release announcement to signing machine, update code
   * (from dev machine: "git push pangea")
   * git checkout master
   * git pull

* create signed tag
   * git tag -s -u meejah@meejah.ca -F release-announce-${VERSION} v${VERSION}

* copy dist/* files + signatures to hidden-service machine
* copy them to the HTML build directory! (docs/_build/html/)

* git pull and build docs there
   * FIXME: why aren't all the dist files copied as part of doc build (only .tar.gz)

* download both distributions + signatures from hidden-service
   * verify sigs
   * verify sha256sums versus announcement text
   * verify tag (git tag --verify v${VERSION}) on machine other than signing-machine
   * run: ./scripts/download-release-onion.sh ${VERSION}

* upload release
   * to PyPI: "make release" (which uses twine so this isn't the same step as "sign the release")
      * make sure BOTH the .tar.gz and .tar.gz.asc (ditto for .whl) are in the dist/ directory first!!)
      * ls dist/txtorcon-${VERSION}*
      * note this depends on a ~/.pypirc file with [server-login] section containing "username:" and "password:"
   * git push origin master
   * git push origin v${VERSION}
   * to github: use web-upload interface to upload the 4 files (both dists, both signature)

* make announcement
   * post to tor-dev@ the clear-signed release announcement
   * post to twisted-python@ the clear-signed release announcement
   * tweet as @txtorcon
   * tell #tor-dev??
