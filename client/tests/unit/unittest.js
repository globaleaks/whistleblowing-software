var assert = require('assert');
var chai = require('chai');
var expect = chai.expect;

var test_data = require('./test_data');

var intervalRef;

beforeEach(window.module('GLUnitTest', function(_$exceptionHandlerProvider_) {
  _$exceptionHandlerProvider_.mode('rethrow');
}));

beforeEach(window.inject(function ($rootScope, $timeout) {
  intervalRef = setInterval(function() {
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


    /* NOTE this skipped test case demonstrates how the unit tests behave with
    it('catchAsyncPromiseThrow', function(done) {
      TestEnv.catchAsyncPromiseThrow().then(function() {
        assert.fail('should never resolve');
      });
    });
    */
  });
});

describe('GLBrowserCrypto', function() {

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
      var keys = glbcCipherLib.loadPublicKeys([test_data.goodKey])
      console.log(keys);
    });

    it('encryptAndSignMessage', function(done) {
      var keys = glbcCipherLib.loadPublicKeys([test_data.goodKey]);
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
    }).timeout(test_data.const.SCRYPT_MAX);

    it('generateCCryptoKey', function(done) {
      var pass = 'Super secret password';

      glbcKeyLib.generateCCryptoKey(pass).then(function(res) {
        console.log('genKeyFinished', res);
        console.log('priv', res.ccrypto_key_private.armor())
        console.log('pub', res.ccrypto_key_public.armor())

        var b = glbcKeyLib.validPublicKey(res.ccrypto_key_public.armor());
        console.log('loaded the following', b);
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('generateKeycode', function() {
       var keycode = glbcKeyLib.generateKeycode();
       console.log(keycode);
       // run 10 times. . .
    });


    it('validPrivateKey', function() {
        var bad_key = '';

        var a = glbcKeyLib.validPrivateKey(test_data.key_ring.priv_key);
        expect(a).to.be.true;
    });

    it('validPublicKey', function() {
      var a = glbcKeyLib.validPublicKey(test_data.badKey);

      expect(a).to.be.false;

      var b = glbcKeyLib.validPublicKey(test_data.goodKey);
      expect(b).to.be.true;
    });

  });

  describe('glbcKeyRing', function() {
    var glbcKeyRing;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_) {
        glbcKeyRing = _glbcKeyRing_;
      });
    });

    it('test initialize and clear', function() {
      expect(glbcKeyRing.isInitialized()).to.be.false;

      console.log(test_data.key_ring.priv_key);
      glbcKeyRing.initialize(test_data.key_ring.priv_key, test_data.key_ring.uuid);

      expect(glbcKeyRing.isInitialized()).to.be.true;

      var a = glbcKeyRing.getPubKey('private');
      var b = glbcKeyRing.getPubKey(test_data.key_ring.uuid);
      var stored = openpgp.key.readArmored(test_data.key_ring.pub_key).keys[0];

      expect(a.primaryKey.fingerprint).to.equal(stored.primaryKey.fingerprint);
      expect(b.primaryKey.fingerprint).to.equal(stored.primaryKey.fingerprint);

      // Add receiver keys to the KeyRing.
      expect(glbcKeyRing.addPubKey.bind(test_data.key_ring.bad_key, 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'))
        .to.throw('Could not add pubkey to key ring!');

      glbcKeyRing.addPubKey(test_data.bob.uuid, test_data.bob.cckey_pub);

      var c = glbcKeyRing.getPubKey(test_data.bob.uuid);

      var bob_pkey = openpgp.key.readArmored(test_data.bob.cckey_pub).keys[0];
      expect(c.primaryKey.fingerprint).to.equal(bob_pkey.primaryKey.fingerprint);
      
      // Test priv_key export protection
      var d = glbcKeyRing.lockKeyRing(test_data.key_ring.passphrase);

      var e = openpgp.key.readArmored(glbcKeyRing.exportPrivKey()).keys[0];
      expect(e.primaryKey.isDecrypted).to.be.false;
      expect(e.primaryKey.fingerprint).to.equal(glbcKeyRing.getKey().primaryKey.fingerprint);

      var f = glbcKeyRing.unlockKeyRing(test_data.key_ring.passphrase);
      expect(f).to.be.true;
      expect(glbcKeyRing.exportPrivKey.bind()).to.throw('Attempted to export decrypted privateKey');

      // Change key passphrase
      glbcKeyRing.changeKeyPassphrase(test_data.key_ring.passphrase, 'fake-passphrase');

      expect(glbcKeyRing.unlockKeyRing(test_data.key_ring.passphrase)).to.be.false;

      expect(glbcKeyRing.unlockKeyRing('fake-passphrase')).to.be.true;

      expect(glbcKeyRing.exportPrivKey.bind()).to.throw('Attempted to export decrypted privateKey');

      // Use getters and setters on a session key
      expect(glbcKeyRing.getSessionKey()).to.equal(null);

      glbcKeyRing.setSessionKey(test_data.submission.sess_cckey_prv_enc);

      expect(glbcKeyRing.getSessionKey().length).to.be.above(100);

      // Test clearing the keyRing
      expect(glbcKeyRing.getPubKey('private')).to.not.be.null;

      glbcKeyRing.clear();

      expect(glbcKeyRing.isInitialized()).to.be.false;
      expect(glbcKeyRing.getPubKey('private')).to.be.null;
      expect(glbcKeyRing.getSessionKey()).to.be.null;
    });
  });

  describe('glbcReceiver', function() {
    var glbcKeyRing, glbcKeyLib, glbcReceiver;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_, _glbcKeyLib_, _glbcReceiver_, _glbcWhistleblower_) {
        glbcKeyRing = _glbcKeyRing_;
        glbcKeyLib = _glbcKeyLib_;
        glbcReceiver = _glbcReceiver_;
        glbcWhistleblower = _glbcWhistleblower_;
      });
    });

    it('receiver should generate master key and use it', function(done) {
      glbcKeyLib.deriveUserPassword(test_data.bob.pass, test_data.bob.salt)
        .then(function(res) {
          return glbcKeyLib.generateCCryptoKey(res.passphrase);
        }).then(function(res) {
          console.log(res.ccrypto_key_private.armor());
          console.log(res.ccrypto_key_public.armor());
          var b = glbcKeyRing.initialize(res.ccrypto_key_private.armor(), test_data.bob.uuid)
          expect(b).to.be.true;
          done();
          return glbcReceiver.loadSessionKey(test_data.submission.sess_cckey_prv_enc);
        }).then(function() {
          done();
        });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('receiver should load master key and use it', function() {

    });

    it('receiver should change master key password', function() {

    });
  });

  describe('glbcWhistleblower', function() {
    var glbcKeyRing, glbcKeyLib, glbcWhistleblower, glbcCipherLib;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_, _glbcKeyLib_, _glbcWhistleblower_, _glbcCipherLib_) {
        glbcKeyRing = _glbcKeyRing_;
        glbcKeyLib = _glbcKeyLib_;
        glbcWhistleblower = _glbcWhistleblower_;
        glbcCipherLib = _glbcCipherLib_;
      });
    });

    it('whistleblower should create an encryption key and a session key', function(done) {
      var submission = {
        wb_cckey_prv_penc: '',
        wb_cckey_pub: '',
        sess_cckey_pub: '',
        sess_cckey_prv_enc: '',
      };

      var keycode = glbcKeyLib.generateKeycode();
      glbcWhistleblower.deriveKey(keycode, test_data.node.receipt_salt, submission).then(function() {

        glbcKeyRing.addPubKey(test_data.bob.uuid, test_data.bob.cckey_pub);
        return glbcWhistleblower.deriveSessionKey([test_data.bob.uuid, 'whistleblower'], submission)
      }).then(function() {

        return glbcWhistleblower.encryptAndSignAnswers(test_data.submission.jsonAnswers, true);
      }).then(function(res) {

        return glbcCipherLib.decryptAndVerifyAnswers(res, true);
      }).then(function(res) {

        expect(res.data).to.equal(test_data.submission.jsonAnswers);
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('whistleblower should reuse an encrypted private key', function(done) {
      glbcKeyLib.deriveUserPassword(test_data.wb.keycode, test_data.node.receipt_salt).then(function(res) {

        glbcWhistleblower.storePassphrase(res.passphrase);
        glbcWhistleblower.initialize(test_data.wb.wb_cckey_prv_penc, []);

        return glbcWhistleblower.unlock();
      }).then(function() {

        return glbcCipherLib.decryptAndVerifyAnswers(test_data.submission.jsonAnswersEnc, true);
      }).then(function(res) {

        expect(res.data).to.equal(test_data.submission.jsonAnswers);
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);
  });

  describe('glbcUserKeyGen', function() {
    it('test state machine', function() {
      // TODO

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
