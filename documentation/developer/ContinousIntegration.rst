=====================
Continous Integration
=====================
The globaleaks codebase is continously tested for bug within a complete continous integration lifecycle implemented.

Testes are performed at every commit by:
* performing static and dynamic testing on `TravisCI <https://travis-ci.org/github/globaleaks/GlobaLeaks>`_;
* performing end2end tests on `SauceLabs <https://saucelabs.com/u/globaleaks>`_ to ensure compatibility with common browsers;
* tracking tests coverage and code quality with `Codacy <https://app.codacy.com/manual/GlobaLeaks/GlobaLeaks>`_.

Backend Tests
=============
The backend testes are implemented by means of python-twisted and trial

Tests can be runned manually by issuing:

.. code:: sh

  cd GlobaLeaks/backend && trial globaleaks

E2E Tests
=========
End2end tests are implemented by means of the Protractor Angular JS library.

Tests can be runned manually by issuing:

.. code:: sh

  cd GlobaLeaks/client && ./node_modules/protractor/bin/protractor tests/protractor.config.js 
