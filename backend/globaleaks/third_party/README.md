# RSTR - xeger

Is a package described here: https://bitbucket.org/leapfrogdevelopment/rstr/ developed 
by Brendam McCollam, and supply one of our GlobaLeaks needs.

Has been downloaded and imported as third party library in our package, because:

  * Is not distributed with easy\_install package
  * Need to be patched for security pourpose.

Is stated in the rstr documentation that:

*rstr uses the Python random module internally to generate psuedorandom text.
This library is not suitable for password-generation or other cryptographic applications.*

but GLBackend is using Crypto.Random safe generation, and then a patch has been applied. 


*In order to help security audit, the integration procedures has been split in these commits*

**downloaded in Dec 10 2014 **: https://bitbucket.org/leapfrogdevelopment/rstr/get/default.zip

**committed unmodified**: https://github.com/globaleaks/GlobaLeaks/commit/

**patch using Crypto.Random**: https://github.com/globaleaks/GlobaLeaks/commit/

# Usage

    import globaleaks.third_party.rstr
    random_output = rstr.xeger('[A-Z]{100}')
