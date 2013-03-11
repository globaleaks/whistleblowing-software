
# RSTR - xeger

Is a package described here: https://bitbucket.org/leapfrogdevelopment/rstr/ developed 
by Brendam McCollam, and supply one of our GlobaLeaks needings. 

Has been downloaded and imported as third party library in our package, because:

  * Is not distributed with easy\_install package
  * Need to be patched for security pourpose.

Is stated in the rstr documentation that:

*rstr uses the Python random module internally to generate psuedorandom text.
This library is not suitable for password-generation or other cryptographic applications.*

but GLBackend is using Crypto.Random safe generation, and then a patch has been applied. 
**In order to help security audit, the integration procedures has been split in commits**

downloaded from, in Mar 8 2013:

https://bitbucket.org/leapfrogdevelopment/rstr/downloads
https://bitbucket.org/leapfrogdevelopment/rstr/get/default.zip

and committed unmodified here:
**[TODO put commit link on github]**

patch using Crypto.Random committed here:
**[TODO put commit link on github]**


