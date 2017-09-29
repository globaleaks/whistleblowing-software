var assert = require('assert');
var chai = require('chai');
var expect = chai.expect;

var intervalRef;

beforeEach(window.module('GLUnitTest', function(_$exceptionHandlerProvider_) {
  _$exceptionHandlerProvider_.mode('log');
}));

beforeEach(angular.mock.inject(function ($rootScope, $timeout) {
  intervalRef = setInterval(function(){
    $rootScope.$apply();
    try {
      $timeout.verifyNoPendingTasks();
    } catch (_) {
      $timeout.flush();
    }
  }, 25);
}));

afterEach(function () {
  clearInterval(intervalRef);
});

describe('GLUnitTest', function() {
  var TestEnv;

  beforeEach(function() {
    window.inject(function(_TestEnv_) {
      TestEnv = _TestEnv_;
    })
  });

  describe('Test Environment', function() {
    it('asyncPromiseTimeout', function(done) {
       TestEnv.asyncPromiseTimeout().then(function(r) {
         done();
       });
    });

    it('asyncPromiseTimeoutErr', function(done) {
       TestEnv.asyncPromiseTimeoutErr().then(function(r) {
          assert.fail('promise must reject')
       }, function(r) {
         done()
       });
    });

    it('syncPromise', function(done) {
       TestEnv.syncPromise().then(function(r) {
         done();
       });
    });

    it('syncPromiseErr', function(done) {
      TestEnv.syncPromiseErr().then(function(r) {
        assert.fail('promise must reject')
      }, function(r) {
        done()
      });
    });
  });
});

describe('GLBrowserCrypto', function() {
  var SCRYPT_MAX = 30000; // maximum timeout for evaluating scrypt

  var goodKey =
    ['-----BEGIN PGP PUBLIC KEY BLOCK-----',
    'Version: GnuPG v2.0.19 (GNU/Linux)',
    '',
    'mI0EUmEvTgEEANyWtQQMOybQ9JltDqmaX0WnNPJeLILIM36sw6zL0nfTQ5zXSS3+',
    'fIF6P29lJFxpblWk02PSID5zX/DYU9/zjM2xPO8Oa4xo0cVTOTLj++Ri5mtr//f5',
    'GLsIXxFrBJhD/ghFsL3Op0GXOeLJ9A5bsOn8th7x6JucNKuaRB6bQbSPABEBAAG0',
    'JFRlc3QgTWNUZXN0aW5ndG9uIDx0ZXN0QGV4YW1wbGUuY29tPoi5BBMBAgAjBQJS',
    'YS9OAhsvBwsJCAcDAgEGFQgCCQoLBBYCAwECHgECF4AACgkQSmNhOk1uQJQwDAP6',
    'AgrTyqkRlJVqz2pb46TfbDM2TDF7o9CBnBzIGoxBhlRwpqALz7z2kxBDmwpQa+ki',
    'Bq3jZN/UosY9y8bhwMAlnrDY9jP1gdCo+H0sD48CdXybblNwaYpwqC8VSpDdTndf',
    '9j2wE/weihGp/DAdy/2kyBCaiOY1sjhUfJ1GogF49rC4jQRSYS9OAQQA6R/PtBFa',
    'JaT4jq10yqASk4sqwVMsc6HcifM5lSdxzExFP74naUMMyEsKHP53QxTF0Grqusag',
    'Qg/ZtgT0CN1HUM152y7ACOdp1giKjpMzOTQClqCoclyvWOFB+L/SwGEIJf7LSCEr',
    'woBuJifJc8xAVr0XX0JthoW+uP91eTQ3XpsAEQEAAYkBPQQYAQIACQUCUmEvTgIb',
    'LgCoCRBKY2E6TW5AlJ0gBBkBAgAGBQJSYS9OAAoJEOCE90RsICyXuqIEANmmiRCA',
    'SF7YK7PvFkieJNwzeK0V3F2lGX+uu6Y3Q/Zxdtwc4xR+me/CSBmsURyXTO29OWhP',
    'GLszPH9zSJU9BdDi6v0yNprmFPX/1Ng0Abn/sCkwetvjxC1YIvTLFwtUL/7v6NS2',
    'bZpsUxRTg9+cSrMWWSNjiY9qUKajm1tuzPDZXAUEAMNmAN3xXN/Kjyvj2OK2ck0X',
    'W748sl/tc3qiKPMJ+0AkMF7Pjhmh9nxqE9+QCEl7qinFqqBLjuzgUhBU4QlwX1GD',
    'AtNTq6ihLMD5v1d82ZC7tNatdlDMGWnIdvEMCv2GZcuIqDQ9rXWs49e7tq1NncLY',
    'hz3tYjKhoFTKEIq3y3Pp',
    '=h/aX',
    '-----END PGP PUBLIC KEY BLOCK-----'].join('\n');

  var badKey = '------ Not a Key -------\nblahblahblah\n-------';

  describe('glbcUtil', function() {
    var glbcUtil;
    beforeEach(function() {
      window.inject(function(_glbcUtil_) {
        glbcUtil = _glbcUtil_;
      });
    });

    it('str2Uint8Array produces real arrays', function() {
      var a = glbcUtil.str2Uint8Array('Hello, world!');
      var b = new Uint8Array([72, 101, 108, 108, 111, 44, 32, 119, 111, 114, 108, 100, 33]);

      a.every(function(val, i) {
        expect(val).to.equal(b[i]);
      });
      expect(a.byteLength).to.equal(b.byteLength);
    });
  });

  describe('glbcCipherLib', function() {
    var glbcCipherLib;
    beforeEach(function() {
      window.inject(function(_glbcCipherLib_) { glbcCipherLib = _glbcCipherLib_; })
    });

    it('loadPublicKeys', function() {
      var keys = glbcCipherLib.loadPublicKeys([goodKey])
      console.log(keys);
    });

    it('encryptAndSignMessage', function(done) {
      var keys = glbcCipherLib.loadPublicKeys([goodKey]);
      var m = 'Hello, world!'
      glbcCipherLib.encryptAndSignMessage(m, keys[0], false).then(function(cipher) {
        console.log('cipher', cipher);
        // TODO key not in keyring
        done();
      });
    });
  });

  describe('glbcKeyLib', function(done) {
    var glbcKeyLib;

    beforeEach(function() {
      window.inject(function(_glbcKeyLib_) {
        glbcKeyLib = _glbcKeyLib_;
      })
    });

    it('deriveUserPassword', function() {
      var pass = 'Super secret password',
          salt = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
      glbcKeyLib.deriveUserPassword(pass, salt).then(function(res) {
        console.log(res);
        done();
      });
    });

    it('scrypt', function(done) {
      var data = 'Super secret password',
          salt = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
          logN = 14,
          dLen = 64;

       glbcKeyLib.scrypt(data, salt, logN, dLen).then(function(res) {
         console.log('scrypted', res);
         done();
       });
    }).timeout(SCRYPT_MAX);

    it('generateCCryptoKey', function(done) {
      var pass = 'Super secret password';

      glbcKeyLib.generateCCryptoKey(pass).then(function(res) {
        console.log('genKeyFinished', res);
        done();
      });
    }).timeout(SCRYPT_MAX);

    it('generateKeycode', function() {
       var keycode = glbcKeyLib.generateKeycode();
       console.log(keycode);
       // run 10 times. . .
    });


    it('validPrivateKey', function() {
        var bad_key = '';
        var good_key = '';
    });

    it('validPublicKey', function() {
      var a = glbcKeyLib.validPublicKey(badKey);

      expect(a).to.equal(false);

      var b = glbcKeyLib.validPublicKey(goodKey);
      expect(b).to.equal(true);
    });

  });

  describe('glbcKeyRing', function() {
    var glbcKeyRing;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_) {
        glbcKeyRing = _glbcKeyRing_;
      });
    });

    it('test life cycle', function() {
      // initialize
      //
      // isInitialiazed
      //
      // add some pub keys
      //
      // getSessionKey
      //
      // try to enc
      //
      // unlockKeyRing
      //
      // enc
      //
      // lockKeyRing
      //
      // try to enc
      //
      // clear
      //
      // check if empty
    });
  });
});

describe('GLClient', function() {

  describe('Utils', function(done) {
    var Utils;

    beforeEach(function() {
      window.inject(function(_Utils_) {
        Utils = _Utils_;
      })
    });

    it('base64DecodeUnicode should handle utf-8 encoded strings', function() {
      var cases = [
        {inp: 'Um9tw6JuaWFJbmNvZ25pdG8=', out: 'RomâniaIncognito'},
        {inp: 'Q3VtIGZ1bmPIm2lvbmVhesSD', out: 'Cum funcționează'},
        {inp: 'w45udHJlYsSDcmkgZnJlY3ZlbnRl', out: 'Întrebări frecvente'},
      ]
      cases.forEach(function(tc) {
        expect(Utils.b64DecodeUnicode(tc.inp)).to.equal(tc.out);
      });
    });
  });
});
