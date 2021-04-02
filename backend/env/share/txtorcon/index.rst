.. txtorcon documentation master file, created by
   sphinx-quickstart on Thu Jan 26 13:04:28 2012.

txtorcon
========

- **docs**:
   - v3 onion: http://fjblvrw2jrxnhtg67qpbzi45r7ofojaoo3orzykesly2j3c2m3htapid.onion/
   - v2 onion: http://timaq4ygg2iegci7.onion
   - clearnet: https://txtorcon.readthedocs.org
- **code**: https://github.com/meejah/txtorcon
- ``torsocks git clone git://timaq4ygg2iegci7.onion/txtorcon.git``
- .. image:: https://travis-ci.org/meejah/txtorcon.png?branch=master
      :target: https://www.travis-ci.org/meejah/txtorcon

  .. image:: https://coveralls.io/repos/meejah/txtorcon/badge.svg
      :target: https://coveralls.io/r/meejah/txtorcon

  .. image:: https://codecov.io/gh/meejah/txtorcon/branch/master/graphs/badge.svg?branch=master
      :target: https://codecov.io/github/meejah/txtorcon?branch=master

  .. image:: https://readthedocs.org/projects/txtorcon/badge/?version=stable
      :target: https://txtorcon.readthedocs.io/en/stable
      :alt: ReadTheDocs

  .. image:: https://readthedocs.org/projects/txtorcon/badge/?version=latest
      :target: https://txtorcon.readthedocs.io/en/latest
      :alt: ReadTheDocs

  .. image:: https://landscape.io/github/meejah/txtorcon/master/landscape.svg?style=flat
      :target: https://landscape.io/github/meejah/txtorcon/master
      :alt: Code Health

.. container:: first_time

    If this is your first time exploring txtorcon, please **look at the**
    :ref:`introduction` **first**. These docs are for version |version|.

.. comment::

    +---------------+---------+---------+
    |   Twisted     | 15.5.0+ | 16.3.0+ |
    +===============+=========+=========+
    |   Python 2.7+ |    ✓    |    ✓    |
    +---------------+---------+---------+
    |   Python 3.5+ |    ✓    |    ✓    |
    +---------------+---------+---------+
    |   PyPy 5.0.0+ |    ✓    |    ✓    |
    +---------------+---------+---------+

Supported and tested platforms: Python 2.7+, Python 3.5+, PyPy 5.0.0+
using Twisted 15.5.0+, 16.3.0+, or 17.1.0+ (see `travis
<https://travis-ci.org/meejah/txtorcon>`_).

**Asycnio inter-operation** is now possible, see :ref:`interop_asyncio`


Documentation
-------------

.. toctree::
   :maxdepth: 3

   introduction
   installing
   guide
   examples
   interop_asyncio
   hacking


Official Releases:
------------------

All official releases are tagged in Git, and signed by my key. All official releases on PyPI have a corresponding GPG signature of the build. Please be aware that ``pip`` does *not* check GPG signatures by default; please see `this ticket <https://github.com/pypa/pip/issues/1035>`_ if you care.

The most reliable way to verify you got what I intended is to clone the Git repository, ``git checkout`` a tag and verify its signature. The second-best would be to download a release + tag from PyPI and verify that.


.. toctree::
   :maxdepth: 2

   releases


API Documentation
-----------------

These are the lowest-level documents, directly from the doc-strings in
the code with some minimal organization; if you're just getting
started with txtorcon **the** ":ref:`programming_guide`" **is a better
place to start**.

.. toctree::
   :maxdepth: 3

   txtorcon


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

