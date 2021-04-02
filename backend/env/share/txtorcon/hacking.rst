.. _hacking:
.. _getting help:

Contributions
=============

You can help contribute to txtorcon by reporting bugs, sending success
stories, by adding a feature or fixing a bug. Even asking that "silly"
question helps me with documentation writing.


.. _contact info:

Contact Information
-------------------

Discussing txtorcon is welcome in the following places:

 - IRC: ``#tor-dev`` on `OFTC <http://www.oftc.net/oftc/>`_ (please
   prefix lines with ``meejah:`` to get my attention, and be patient
   for replies).
 - email: preferably on the `tor-dev
   <https://lists.torproject.org/cgi-bin/mailman/listinfo/tor-dev>`_
   list, or see `meejah.ca <https://meejah.ca/contact>`_ for other ways
   to contact me.
 - bugs: use `txtorcon's issues
   <https://github.com/meejah/txtorcon/issues>`_ tracker on GitHub.
 - `@txtorcon <https://twitter.com/txtorcon>`_ on Twitter (announcements only)


Public Key
----------

You can download my key from a keyserver (`0xC2602803128069A7
<http://pgp.mit.edu:11371/pks/lookup?op=get&search=0xC2602803128069A7>`_)
or see :download:`meejah.asc <../meejah.asc>` in the repository. The fingerprint
is ``9D5A 2BD5 688E CB88 9DEB CD3F C260 2803 1280 69A7``.

Also available at `https://meejah.ca/meejah.asc <https://meejah.ca/meejah.asc>`_.
For convenience: ``curl https://meejah.ca/meejah.asc | gpg --import``


Pull Requests
-------------

Yes, please!

If you have a new feature or a bug fix, the very best way is to submit
a pull-request on GitHub. Since we have 100% coverage, all new lines
of code should at least be covered by unit-tests. You can also include
a note about the change in ``docs/releases.rst`` if you like (or I can
make one up after the merge).

I prefer if you rebase/squash commits into logical chunks. Discussion
of any implementation details can simply occur on the pull-request
itself. Force-pushing to the same branch/PR is fine by me if you want
to re-order commits etcetera (but, it's also fine if you just want to
push new "fix issues" commits instead).

Some example pull-requests:

  * good discussion + more commits: `PR #150 <https://github.com/meejah/txtorcon/pull/150>`_;
  * a simple one that was "ready-to-go": `PR #51 <https://github.com/meejah/txtorcon/pull/51>`_.

If you want an easy thing to start with, here are `all issues tagged
"easy" <https://github.com/meejah/txtorcon/labels/easy_ticket>`_


Making a Release
----------------

Mostly a note-to-self, but here is my release checklist.

.. toctree::
   :maxdepth: 3

   release-checklist
