Home-page: https://github.com/meejah/txtorcon
Author: meejah
Author-email: meejah@meejah.ca
License: MIT
Description: 
        
        
        
        
        .. _NOTE: see docs/index.rst for the starting-point
        .. _ALSO: https://txtorcon.readthedocs.org for rendered docs
        
        
        
        
        
        
        .. image:: https://travis-ci.org/meejah/txtorcon.png?branch=master
            :target: https://www.travis-ci.org/meejah/txtorcon
            :alt: travis
        
        .. image:: https://coveralls.io/repos/meejah/txtorcon/badge.png
            :target: https://coveralls.io/r/meejah/txtorcon
            :alt: coveralls
        
        .. image:: http://codecov.io/github/meejah/txtorcon/coverage.svg?branch=master
            :target: http://codecov.io/github/meejah/txtorcon?branch=master
            :alt: codecov
        
        .. image:: https://readthedocs.org/projects/txtorcon/badge/?version=stable
            :target: https://txtorcon.readthedocs.io/en/stable
            :alt: ReadTheDocs
        
        .. image:: https://readthedocs.org/projects/txtorcon/badge/?version=latest
            :target: https://txtorcon.readthedocs.io/en/latest
            :alt: ReadTheDocs
        
        .. image:: http://api.flattr.com/button/flattr-badge-large.png
            :target: http://flattr.com/thing/1689502/meejahtxtorcon-on-GitHub
            :alt: flattr
        
        .. image:: https://landscape.io/github/meejah/txtorcon/master/landscape.svg?style=flat
            :target: https://landscape.io/github/meejah/txtorcon/master
            :alt: Code Health
        
        
        txtorcon
        ========
        
        - **docs**: https://txtorcon.readthedocs.org or http://timaq4ygg2iegci7.onion
        - **code**: https://github.com/meejah/txtorcon
        - ``torsocks git clone git://timaq4ygg2iegci7.onion/txtorcon.git``
        - MIT-licensed;
        - Python 2.7, PyPy 5.0.0+, Python 3.4+;
        - depends on
          `Twisted`_,
          `Automat <https://github.com/glyph/automat>`_,
          (and the `ipaddress <https://pypi.python.org/pypi/ipaddress>`_ backport for non Python 3)
        
        .. caution::
        
          Several large, new features have landed on master. If you're working
          directly from master, note that some of these APIs may change before
          the next release.
        
        
        Ten Thousand Feet
        -----------------
        
        txtorcon is an implementation of the `control-spec
        <https://gitweb.torproject.org/torspec.git/blob/HEAD:/control-spec.txt>`_
        for `Tor <https://www.torproject.org/>`_ using the `Twisted`_
        networking library for `Python <http://python.org/>`_.
        
        This is useful for writing utilities to control or make use of Tor in
        event-based Python programs. If your Twisted program supports
        endpoints (like ``twistd`` does) your server or client can make use of
        Tor immediately, with no code changes. Start your own Tor or connect
        to one and get live stream, circuit, relay updates; read and change
        config; monitor events; build circuits; create onion services;
        etcetera (`ReadTheDocs <https://txtorcon.readthedocs.org>`_).
        
        
        Some Possibly Motivational Example Code
        ---------------------------------------
        
        `download <examples/readme.py>`_
        (also `python3 style <examples/readme3.py>`_)
        
        .. code:: python
        
            from twisted.internet.task import react
            from twisted.internet.defer import inlineCallbacks
            from twisted.internet.endpoints import UNIXClientEndpoint
            import treq
            import txtorcon
        
            @react
            @inlineCallbacks
            def main(reactor):
                tor = yield txtorcon.connect(
                    reactor,
                    UNIXClientEndpoint(reactor, "/var/run/tor/control")
                )
        
                print("Connected to Tor version {}".format(tor.version))
        
                url = 'https://www.torproject.org:443'
                print("Downloading {}".format(url))
                resp = yield treq.get(url, agent=tor.web_agent())
        
                print("   {} bytes".format(resp.length))
                data = yield resp.text()
                print("Got {} bytes:\n{}\n[...]{}".format(
                    len(data),
                    data[:120],
                    data[-120:],
                ))
        
                print("Creating a circuit")
                state = yield tor.create_state()
                circ = yield state.build_circuit()
                yield circ.when_built()
                print("  path: {}".format(" -> ".join([r.ip for r in circ.path])))
        
                print("Downloading meejah's public key via above circuit...")
                resp = yield treq.get(
                    'https://meejah.ca/meejah.asc',
                    agent=circ.web_agent(reactor, tor.config.socks_endpoint(reactor)),
                )
                data = yield resp.text()
                print(data)
        
        
        
        Try It Now On Debian/Ubuntu
        ---------------------------
        
        For example, serve some files via an onion service (*aka* hidden
        service):
        
        .. code-block:: shell-session
        
            $ sudo apt-get install --install-suggests python-txtorcon
            $ twistd -n web --port "onion:80" --path ~/public_html
        
        
        Read More
        ---------
        
        All the documentation starts `in docs/index.rst
        <docs/index.rst>`_. Also hosted at `txtorcon.rtfd.org
        <https://txtorcon.readthedocs.io/en/latest/>`_.
        
        You'll want to start with `the introductions <docs/introduction.rst>`_ (`hosted at RTD
        <https://txtorcon.readthedocs.org/en/latest/introduction.html>`_).
        
        .. _Twisted: https://twistedmatrix.com/trac
        
Keywords: python,twisted,tor,tor controller
Platform: UNKNOWN
Classifier: Framework :: Twisted
Classifier: Development Status :: 4 - Beta
Classifier: Intended Audience :: Developers
Classifier: License :: OSI Approved :: MIT License
Classifier: Natural Language :: English
Classifier: Operating System :: POSIX :: Linux
Classifier: Operating System :: Unix
Classifier: Programming Language :: Python
Classifier: Programming Language :: Python :: 2
Classifier: Programming Language :: Python :: 2.6
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Classifier: Topic :: Internet :: Proxy Servers
Classifier: Topic :: Internet
Classifier: Topic :: Security
Provides-Extra: dev
