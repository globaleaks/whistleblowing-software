.. _installing:

Installing txtorcon
===================

Latest Release
--------------

txtorcon is on PyPI and in Debian since `jessie
<https://packages.debian.org/jessie/python-txtorcon>`_ (thanks to
Lunar and now `irl
<https://qa.debian.org/developer.php?login=irl@debian.org>`_!). So,
one of these should work:

- install latest release: ``pip install txtorcon``
- Debian or Ubuntu: ``apt-get install python-txtorcon``
- Watch an `asciinema demo <http://asciinema.org/a/5654>`_ for an overview.

Rendered documentation for the latest release is at
`txtorcon.readthedocs.org <https://txtorcon.readthedocs.org/en/latest/>`_. What exists for
release-notes are in ":ref:`releases`".

If you're still using wheezy, ``python-txtorcon`` is also in `wheezy-backports <http://packages.debian.org/source/wheezy-backports/txtorcon>`_. To install, do this as root:

.. sourcecode:: shell-session

    # echo "deb http://ftp.ca.debian.org/debian/ wheezy-backports main" >> /etc/apt/sources.list
    # apt-get update
    # apt-get install python-txtorcon

It also `appears txtorcon is in Gentoo
<http://packages.gentoo.org/package/net-libs/txtorcon>`_ but I don't
use Gentoo (if anyone has a shell-snippet that installs it, send a
pull-request). I am told this package also needs a maintainer;
see XXX.

**Installing the wheel files** requires a recent pip and
setuptools. At least on Debian, it is important to upgrade setuptools
*before* pip. This procedure appears to work fine::

   virtualenv foo
   . foo/bin/activate
   pip install --upgrade setuptools
   pip install --upgrade pip
   pip install path/to/txtorcon-*.whl


If you get an error like `SyntaxError: invalid syntax` on
`txtorcon/test/py3_torstate.py` or similar, you have an out-of-date
pip or setuptools; see above.


Compatibility
-------------

txtorcon runs all tests cleanly under Python2, Python3 and PyPy on:

  -  Debian: "squeeze", "wheezy" and "jessie"
  -  OS X: 10.4 (naif), 10.8 (lukas lueg), 10.9 (kurt neufeld)
  -  Fedora 18 (lukas lueg)
  -  FreeBSD 10 (enrique fynn) (**needed to install "lsof"**)
  -  RHEL6
  -  **Reports from other OSes appreciated.**


.. _configure_tor:

Tor Configuration
-----------------

Using Tor's cookie authentication is the most convenient way to
connect; this proves that your user can read a cookie file written by
Tor. To enable this, you'll want to have the following options on in
your ``torrc``::

   CookieAuthentication 1
   CookieAuthFileGroupReadable 1

Note that "Tor BrowserBundle" is configured this way by default, on
port 9151.  If you want to use unix sockets to speak to tor (highly
recommended) add this to your config (Debian is already set up like
this)::

   ControlSocketsGroupWritable 1
   ControlSocket /var/run/tor/control


Source Code
-----------

Most people will use the code from https://github.com/meejah/txtorcon
The canonical URI is http://timaq4ygg2iegci7.onion
I sign tags with my public key (:download:`meejah.asc <../meejah.asc>`)

- ``git clone https://github.com/meejah/txtorcon.git``
- ``torsocks git clone git://timaq4ygg2iegci7.onion/meejah/txtorcon.git``

Rendered documentation for the latest release is at `txtorcon.readthedocs.org <https://txtorcon.readthedocs.org/en/latest/>`_.

See :ref:`hacking` if you wish to contribute back to txtorcon :)


Development Environment
-----------------------

I like to set up my Python development like this:

.. code-block:: shell-session

    $ git clone https://github.com/meejah/txtorcon.git
    $ echo "if you later fork it on github, do this:"
    $ git remote add -f github git+ssh://git@github.com/<your github handle>/txtorcon.git
    $ cd txtorcon
    $ virtualenv venv
    $ source venv/bin/activate
    (venv)$ pip install --editable .[dev]  # "dev" adds more deps, like Sphinx
    (venv)$ make doc
    (venv)$ make test
    (venv)$ tox  # run all tests, in all supported configs

You can now edit code in the repository as normal. To submit a patch,
the easiest way is to "clone" the txtorcon project, then "fork" on
github and add a remote called "github" with your copy of the code to
which you can push (``git remote add -f github
git+ssh://git@github.com/<your github handle>/txtorcon.git``). The
``-f`` is so you don't have to run ``git fetch`` right after.

Now, you can push a new branch you've made to GitHub with ``git push
github branch-name`` and then examine it and open a pull-request. This
will trigger Travis to run the tests, after which coverage will be
produced (and a bot comments on the pull-request). If you require any
more changes, the easiest thing to do is just commit them and push
them. (If you know how, re-basing/re-arranging/squashing etc is nice
to do too). See :ref:`hacking` for more.


Integration Tests
-----------------

There are a couple of simple integration tests using Docker in the
``integration/`` directory; these make a ``debootstrap``-built base
image and then do the test inside containers cloned from this -- no
trusting ``https://docker.io`` required. See ``integration/README``
for more information.

If you're on Debian, there's a decent chance running ``make
txtorcon-tester`` followed by ``make integration`` from the root of
the checkout will work (the first commands ultimately runs
``debootstrap`` and some ``apt`` commands besides ``docker`` things).


.. _dependencies:

Dependencies / Requirements
---------------------------

These should have been installed by whichever method you chose above,
but are listed here for completeness. You can get all the development
requirements with e.g. ``pip install txtorcon[dev]``.

- `twisted <http://twistedmatrix.com>`_: txtorcon should work with any
  Twisted 11.1.0 or newer. Twisted 15.4.0+ works with Python3, and so
  does txtorcon (if you find something broken on Py3 please file a
  bug).

- `automat <https://github.com/glyph/automat>`_: "a library for
  concise, idiomatic Python expression of finite-state automata
  (particularly deterministic finite-state transducers)."

- `ipaddress <https://docs.python.org/3/library/ipaddress.html>`_: a
  standard module in Python3, but requires installing the backported
  package on Python2.

- **dev only**: `Sphinx <http://sphinx.pocoo.org/>`_ if you want to
  build the documentation. In that case you'll also need something
  called ``python-repoze.sphinx.autointerface`` (at least in Debian)
  to build the Interface-derived docs properly.

- **dev only**: `coverage <http://nedbatchelder.com/code/coverage/>`_
  to run the code-coverage metrics.

- **dev only** `cuv'ner <https://cuvner.readthedocs.io/en/latest/>`_
  for coverage visualization

- **dev only**: `Tox <https://testrun.org/tox/latest/>`_ to run
  different library revisions.

- **dev optional**: `GraphViz <http://www.graphviz.org/>`_ is used in the
  tests (and to generate state-machine diagrams, if you like) but
  those tests are skipped if "dot" isn't in your path

.. BEGIN_INSTALL

In any case, on a `Debian <http://www.debian.org/>`_ wheezy, squeeze or
Ubuntu system, this should work (as root):

.. sourcecode:: shell-session

  # apt-get install -y python-setuptools python-twisted python-ipaddress graphviz tor
  # echo "for development:"
  # apt-get install -y python-sphinx python-repoze.sphinx.autointerface python-coverage libgeoip-dev

.. END_INSTALL

Using pip this would be:

.. sourcecode:: shell-session 

  $ pip install --user Twisted ipaddress pygeoip
  $ echo "for development:"
  $ pip install --user GeoIP Sphinx repoze.sphinx.autointerface coverage

or:

.. sourcecode:: shell-session
		
    $ pip install -r requirements.txt
    $ pip install -r dev-requirements.txt
