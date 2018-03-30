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
       TestEnv.syncPromise().then(function() {
         done();
       });
    });

    it('syncPromiseErr', function(done) {
      TestEnv.syncPromiseErr().then(function() {
        assert.fail('promise must reject')
      }, function() {
        done()
      });
    });

    it('asyncPromiseTimeout', function(done) {
       TestEnv.asyncPromiseTimeout().then(function() {
         done();
       });
    });

    it('asyncPromiseTimeoutErr', function(done) {
       TestEnv.asyncPromiseTimeoutErr().then(function() {
         assert.fail('promise must reject')
       }, function() {
         done()
       });
    });

    /*
    // NOTE this skipped test case demonstrates how the unit tests behave with
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
        return true;
      });
      expect(a.byteLength).to.equal(b.byteLength);
    });
  });

  describe('glbcCipherLib', function() {
    var glbcCipherLib, glbcKeyRing;
    beforeEach(function() {
      window.inject(function(_glbcCipherLib_, _glbcKeyRing_) {
        glbcCipherLib = _glbcCipherLib_;
        glbcKeyRing = _glbcKeyRing_;
      })
    });

    it('loadPublicKeys', function() {
      var keys = glbcCipherLib.loadPublicKeys([test_data.key_ring.pub_key, test_data.bob.cckey_pub])

      for (var i = 0; i < keys.length; i++) {
        expect(keys[i].isPrivate()).to.be.false;
      }
    });

    it('encryptAndSignMessage', function(done) {
      glbcKeyRing.initialize(test_data.key_ring.priv_key, test_data.key_ring.uuid).then(function() {
        var uuid = 'faceface-face-face-facefaceface';
        glbcKeyRing.addPubKey(uuid, test_data.key_ring.pub_key).then(function() {
          var m = 'Hello, world!'
          glbcCipherLib.encryptAndSignMessage(m, uuid, false).then(function(cipher) {
            var m = openpgp.message.readArmored(cipher);
            expect(m).to.not.be.null;
            done();
          });
        });
      });
    });
  });

  describe('glbcKeyLib', function() {
    var glbcKeyLib, glbcUtil;

    beforeEach(function() {
      window.inject(function(_glbcKeyLib_, _glbcUtil_) {
        glbcKeyLib = _glbcKeyLib_;
        glbcUtil = _glbcUtil_;
      })
    });

    it('deriveUserPassword', function(done) {
      glbcKeyLib.deriveUserPassword(test_data.cc_lib.scrypt.passphrase,
                                    test_data.cc_lib.scrypt.salt
                                   ).then(function(res) {
        expect(res.passphrase).to.equal(test_data.cc_lib.scrypt.digest);
        expect(res.authentication).to.equal(test_data.cc_lib.scrypt.hash_digest)
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('scrypt', function(done) {
      var dLen = 64;

       glbcKeyLib.scrypt(test_data.cc_lib.scrypt.passphrase,
                         test_data.cc_lib.scrypt.salt,
                         test_data.cc_lib.scrypt.logN,
                         dLen
                        ).then(function(res) {

         var hex = glbcUtil.bin2hex(res.stretched);
         expect(hex).to.equal(test_data.cc_lib.scrypt.digest);
         done();
       });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('generateCCryptoKey', function(done) {
      glbcKeyLib.generateCCryptoKey(test_data.cc_lib.scrypt.passphrase).then(function(res) {
        expect(res.ccrypto_key_public.isPrivate()).to.be.false;
        expect(res.ccrypto_key_private.isPrivate()).to.be.true;
        expect(res.ccrypto_key_private.primaryKey.isDecrypted).to.be.false;
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);

    it('generateKeycode', function(done) {
      glbcKeyLib.generateKeycode().then(function(keycode) {
        expect(/^[0-9]{16}$/.test(keycode)).to.be.true;
        done();
      });
    });

    it('validPrivateKey', function(done) {
      glbcKeyLib.validPrivateKey(test_data.key_ring.bad_key).then(function() {
      }, function () {
        // fail
        glbcKeyLib.validPrivateKey(test_data.key_ring.pub_key).then(function() {
        }, function () {
          // fail
          glbcKeyLib.validPrivateKey(test_data.key_ring.priv_key).then(function() {
            //success
            done();
          });
        });
      });
    });

    it('validPublicKey', function() {
      glbcKeyLib.validPublicKey(test_data.key_ring.bad_key).then(function() {
      }, function () {
        // fail
        glbcKeyLib.validPublicKey(test_data.key_ring.priv_key).then(function() {
        }, function () {
          // fail
          glbcKeyLib.validPublicKey(test_data.key_ring.pub_key).then(function() {
            //success
            done();
          });
        });
      });
    });
  });

  describe('glbcKeyRing', function() {
    var glbcKeyRing;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_) {
        glbcKeyRing = _glbcKeyRing_;
      });
    });

    it('test initialize and clear', function(done) {
      expect(glbcKeyRing.isInitialized()).to.be.false;

      glbcKeyRing.initialize(test_data.key_ring.priv_key, test_data.key_ring.uuid).then(function() {
        expect(glbcKeyRing.isInitialized()).to.be.true;

        var a = glbcKeyRing.getPubKey('private');
        var b = glbcKeyRing.getPubKey(test_data.key_ring.uuid);
        var stored = openpgp.key.readArmored(test_data.key_ring.pub_key).keys[0];

        expect(a.primaryKey.fingerprint).to.equal(stored.primaryKey.fingerprint);
        expect(b.primaryKey.fingerprint).to.equal(stored.primaryKey.fingerprint);

        // Add receiver keys to the KeyRing.
        glbcKeyRing.addPubKey(test_data.key_ring.bad_key, 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb').then(function() {
        }, function() {
          glbcKeyRing.addPubKey(test_data.bob.uuid, test_data.bob.cckey_pub).then(function() {
            var c = glbcKeyRing.getPubKey(test_data.bob.uuid);

            var bob_pkey = openpgp.key.readArmored(test_data.bob.cckey_pub).keys[0];
            expect(c.primaryKey.fingerprint).to.equal(bob_pkey.primaryKey.fingerprint);

            // Test priv_key export protection
            glbcKeyRing.lockKeyRing(test_data.key_ring.passphrase).then(function() {

              var d = openpgp.key.readArmored(glbcKeyRing.exportPrivKey()).keys[0];
              expect(d.primaryKey.fingerprint).to.equal(glbcKeyRing.getKey().primaryKey.fingerprint);

              // Change key passphrase
              glbcKeyRing.changeKeyPassphrase(test_data.key_ring.passphrase, 'fake-passphrase').then(function() {
                glbcKeyRing.unlockKeyRing('fake-passphrase').then(function() {
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

                  done();
                });
              });
            });
          });
        });
      });
    });
  });

  describe('glbcReceiver', function() {
    var glbcKeyRing, glbcKeyLib, glbcReceiver;
    beforeEach(function() {
      window.inject(function(_glbcKeyRing_, _glbcKeyLib_, _glbcReceiver_) {
        glbcKeyRing = _glbcKeyRing_;
        glbcKeyLib = _glbcKeyLib_;
        glbcReceiver = _glbcReceiver_;
      });
    });

    it('receiver should generate master key and use it', function(done) {
      glbcKeyLib.deriveUserPassword(test_data.bob.pass, test_data.bob.salt)
        .then(function(res) {
          return glbcKeyLib.generateCCryptoKey(res.passphrase);
        }).then(function(res) {
          return glbcKeyRing.initialize(res.ccrypto_key_private.armor(), test_data.bob.uuid).then(function() {
            // TODO: generate a tip session key and simulate its use
            done();
          });
        });
    }).timeout(test_data.const.SCRYPT_MAX);

    it.skip('receiver should encrypt and decrypt messages', function() {

    });

    it.skip('receiver should encrypt and decrypt comments', function() {

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

      glbcKeyLib.generateKeycode().then(function(keycode) {
        return glbcWhistleblower.deriveKey(keycode, test_data.node.receipt_salt, submission).then(function() {
          return glbcKeyRing.addPubKey(test_data.bob.uuid, test_data.bob.cckey_pub).then(function() {
            return glbcWhistleblower.deriveSessionKey([test_data.bob.uuid, 'whistleblower'], submission)
          });
        }).then(function() {
          return glbcWhistleblower.encryptAndSignAnswers(test_data.submission.jsonAnswers, true);
        }).then(function(res) {
          return glbcCipherLib.decryptAndVerifyAnswers(res, true);
        }).then(function(res) {
          expect(res.data).to.equal(test_data.submission.jsonAnswers);
          done();
        });
      });
    }).timeout(test_data.const.SCRYPT_MAX*2);

    it('whistleblower should reuse an encrypted private key', function(done) {
      glbcKeyLib.deriveUserPassword(test_data.wb.keycode, test_data.node.receipt_salt).then(function(res) {
        glbcWhistleblower.storePassphrase(res.passphrase);
        return glbcWhistleblower.initialize(test_data.wb.wb_cckey_prv_penc, []).then(function() {
          return glbcWhistleblower.unlock();
        });
      }).then(function() {
        return glbcCipherLib.decryptAndVerifyAnswers(test_data.submission.jsonAnswersEnc, true);
      }).then(function(res) {
        expect(res.data).to.equal(test_data.submission.jsonAnswers);
        done();
      });
    }).timeout(test_data.const.SCRYPT_MAX);

    it.skip('whistleblower should encrypt and decrypt messages', function() {

    });

    it.skip('whistleblower should encrypt and decrypt comments', function() {

    });
  });

  describe('glbcUserKeyGen', function() {
    var glbcUserKeyGen, Authentication;
    beforeEach(function() {
      window.inject(function(_glbcUserKeyGen_, _Authentication_) {
        glbcUserKeyGen = _glbcUserKeyGen_;
        Authentication = _Authentication_;
      });
    });

    it('WizardKeyGen', function(done) {
       Authentication.user_salt = test_data.key_gen.user_salt;
       glbcUserKeyGen.vars.keyGen = true;

       glbcUserKeyGen.setup();

       // Use wizard to avoid the http post to the backend
       glbcUserKeyGen.wizardStartKeyGen();

       glbcUserKeyGen.addPassphrase('unused', test_data.key_gen.passphrase);

       glbcUserKeyGen.vars.promises.ready.then(function(resp) {
         expect(resp.old_auth_token_hash.length).to.equal(128);
         expect(resp.new_auth_token_hash.length).to.equal(128);
         expect(resp.new_auth_token_hash).to.equal(test_data.key_gen.authentication);

         var pub_key = openpgp.key.readArmored(resp.cckey_pub).keys[0];
         expect(pub_key.isPrivate()).to.be.false;

         var priv_key = openpgp.key.readArmored(resp.cckey_prv_penc).keys[0];
         expect(priv_key.isPrivate()).to.be.true;

         expect(priv_key.primaryKey.isDecrypted).to.be.false;
         priv_key.decrypt(test_data.key_gen.scrypt_passphrase).then(function() {
           expect(priv_key.primaryKey.isDecrypted).to.be.true;
           done();
         });
       });
    }).timeout(test_data.const.SCRYPT_MAX*2);
  });
});

describe('GLClient', function() {
  describe('Utils', function() {
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
