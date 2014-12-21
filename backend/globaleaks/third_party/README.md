# RSTR - xeger

Is a package described here: https://bitbucket.org/leapfrogdevelopment/rstr/ developed 
by Brendam McCollam, and supply one of our GlobaLeaks needs.

Has been downloaded and imported as third party library in our package, because:

  * Is not distributed with easy\_install package
  * Need to be patched for security pourpose.

Is stated in the rstr documentation that:

*rstr uses the Python random module internally to generate psuedorandom text so
this library is not suitable for password-generation or other cryptographic applications.*

instead in GlobaLeaks it's used os.urandom for safe generation, and then a patch has been applied.

*In order to help security audit, the integration procedures has been split in these commits*

**downloaded in Dec 10 2014 **: https://bitbucket.org/leapfrogdevelopment/rstr/get/default.zip

**committed unmodified**: https://github.com/globaleaks/GlobaLeaks/commit/d2876d782fbb8fc4ac0170a721ab2610590536d4

**patched using os.random**: https://github.com/globaleaks/GlobaLeaks/commit/3c23797bbb17c988696bf566df0a66748aee66a

# Usage

    import globaleaks.third_party.rstr
    random_output = rstr.xeger('[A-Z]{100}')
