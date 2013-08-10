# Security of the Submission System

SCOPE: This page will go on initiatives website, and needs to explain why
globaleaks is secure without expecting the reader to have strong prior
security knowledge.

This Whistleblowing Submission platform is implemented using the 
[GlobaLeaks Software](https://globaleaks.org) and anonymity for the
whistleblower is provided thanks to [Tor software](https://torproject.org/). 

Tor is the state of the art when it comes to digitally protecting anonymity and
has received a 
[lot of](http://systems.cs.colorado.edu/~bauerk/papers/wpes25-bauer.pdf)
attention
[from](https://svn.torproject.org/svn/projects/design-paper/tor-design.pdf)
both
[the](http://www.cl.cam.ac.uk/users/sjm217/papers/oakland05torta.pdf)
[academic](http://www.onion-router.net/Publications/locating-hidden-servers.pdf) research
[community](http://www.cypherpunks.ca/~iang/pubs/torsec.pdf) and
[experts](http://www.crhc.uiuc.edu/~nikita/papers/tuneup-cr.pdf)
in 
[the field](http://freehaven.net/anonbib/papers/congestion-longpaths.pdf)
of
[IT security](http://www.ieee-security.org/TC/SP2013/papers/4977a080.pdf).

GlobaLeaks is the first opensource, secure and anonymous whistleblowing
platform designed by the [Hermes Center](http://logioshermes.org/)
for Transparency and Digital Human Rights.

Tor is already integrated into GlobaLeaks, that way the Site Owner is not able
to have any kind of traces or information about the Whistleblower's identity or
location.

You can never never be sure if somebody will do some further investigation
about your submission, for this reason we recommend to ensure the maximum level
of security and privacy possible.

The easiest way to use Tor is by downloading the Tor Browser Bundle: an
anonymous internet browser.

If you can't or don't want to use the Tor Browser Bundle to do submission
anonymously, you can do it as a "Confidential Submission" thanks to the use of
[Tor2Web](https://tor2web.org/), an Internet-to-Tor proxy service.
Tor2web allows the user to access the site even without having Tor installed on
their system. If the whistleblower is worried about somebody reading their
network traffic they should not submit over tor2web. We discourage to perform
submissions over tor2web and it should only be done when the whistleblower is
fully aware of the risks.

Complete security can never be guaranteed, however we have designed this
technology with in mind scenarios where the life of the whistleblower is at
stake.

Security experts have performed multiple audits on our software to identify and
fix possible vulnerabilities. This is the only way to ensure that the
application is truly secure. We do not only tell you to trust us to have made
the right decisions, but have received various independent analysis from third
parties. 

Moreover the source code of GlobaLeaks is open, therefore anybody can inspect
it and make sure that it does what we say it does.

For more in depth analysis of the security of GlobaLeaks see:
[GlobaLeaks Application SecurityDesign and Details](https://docs.google.com/document/d/1SMSiAry7x5XY9nY8GAejJD75NWg7bp7M1PwXSiwy62U/pub)
and
[GlobaLeaks threat model](https://docs.google.com/document/d/1niYFyEar1FUmStC03OidYAIfVJf18ErUFwSWCmWBhcA/pub)
