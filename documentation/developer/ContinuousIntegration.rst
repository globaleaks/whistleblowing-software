====================
Continuous Integration
====================
The globaleaks codebase is continuously tested for bug within a complete continuous integration lifecycle implemented.

Testes are performed at every commit by:

* performing static and dynamic testing on `TravisCI <https://travis-ci.org/github/globaleaks/GlobaLeaks>`_;
* performing end2end tests on `SauceLabs <https://saucelabs.com/u/globaleaks>`_ to ensure compatibility with common browsers;
* tracking tests coverage and code quality with `Codacy <https://app.codacy.com/manual/GlobaLeaks/GlobaLeaks>`_.

Unit Tests
==========
Unit tests are implemented by means of python-twisted and trial

Tests can be run manually by issuing:

.. code:: sh

  cd GlobaLeaks/backend && trial globaleaks

E2E Tests
=========
End to end tests are implemented by means of the Protractor Angular JS library.

Tests can be run manually by issuing:

.. code:: sh

  cd GlobaLeaks/client && ./node_modules/protractor/bin/protractor tests/protractor.config.js 
