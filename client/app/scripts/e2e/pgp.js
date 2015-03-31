angular.module('e2e', []).
  factory('pgp', [], function() {
    return {
      generate_key: function(cb) {
        var email = 'a@b.org';
        var password = 'abc123';

        var k_user_id = email;
        var k_passphrase = password;
        var k_bits = 4096;
        var k_bits = 2048;

        openpgp.config.show_comment = false;
        openpgp.config.show_version = false;

        var key = openpgp.generateKeyPair({
          numBits: k_bits, userId: k_user_id,
          //passphrase: k_passphrase
        }).then(function(keyPair) {
          var zip = new JSZip();
          var user_id = k_user_id.replace("@", "_at_");
          var user_id = user_id.replace(".", "_dot_");
          var folder_name = "globaleaks-keys-" + user_id
          var file_name = folder_name + '.zip'

          var keys = zip.folder(folder_name);
          keys.file("private.asc", keyPair.privateKeyArmored);
          keys.file("public.asc", keyPair.publicKeyArmored);

          var content = zip.generate({type:"blob"});
          cb(keyPair, content);
        });
      }
    }
});
