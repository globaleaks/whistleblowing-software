var GLCrypto = {};

GLCrypto.getRandomBytes = function () {
  // This code is taken from cryptocat.
  var buffer, crypto;
  // Node.js ... for tests
  if (typeof window === 'undefined' && typeof require !== 'undefined') {
    crypto = require('crypto');
    try {
      buffer = crypto.randomBytes(40)
    } catch (e) {
      throw e
    }
  }
  // Older versions of Firefox
  else if (navigator.userAgent.match('Firefox') &&
    (!window.crypto || !window.crypto.getRandomValues)
    ) {
    var element = document.createElement('cryptocatFirefoxElement');
    document.documentElement.appendChild(element);
    var evt = document.createEvent('HTMLEvents');
    evt.initEvent('cryptocatGenerateRandomBytes', true, false);
    element.dispatchEvent(evt);
    buffer = element.getAttribute('randomValues').split(',');
    element = null
  }
  // Browsers that don't require workarounds
  else {
    buffer = new Uint8Array(40);
    window.crypto.getRandomValues(buffer)
  }
  return buffer
};

GLCrypto.randomString = function (length) {
  var possibleChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    randomBytes = GLCrypto.getRandomBytes(),
    result = '';

  for (var i = 0; i < length; i++) {
    var idx = i;
    // If we have already covered all possible values then we need to generate
    // some new bytes.
    if (idx > randomBytes.length) {
      randomBytes = GLCrypto.getRandomBytes();
      idx = idx % randomBytes.length;
    }
    ;
    result += possibleChars[randomBytes[idx] % possibleChars.length];
  }
  ;
  return result;
};

