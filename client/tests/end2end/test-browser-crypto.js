
describe('GLBrowserCrypto module', function() {
  it('should be able to generate a key pair', function() {
    // Generate a pgp key pair here.
    var receipt = gbcKeyFunc.generate_keycode();
    console.log("The WB's receipt:", receipt);
    gbcKeyFunc.generate_e2e_key(receipt).then(function(key_pair) {
      console.log("Generated a new key pair!", key_pair);
       
      var fakeFile = new File([new Blob(['Hello, world! This is something Id like to show you!'])], 'blob.txt' );
      console.log('Input file:', fakeFile);
      encryptedFileRead(fakeFile).then(function(ciphertext) {
        console.log('Encrypted result:', ciphertext);
      });

      function encryptedFileRead(file) {
        var deferred = $q.defer();
        createFileArray(file).then(function(fileArr) {
          // Get the public keys for each receiver
          //var pubKeyStrs = $scope.receivers.map(function(rec) { return rec.pgp_key_public; });
          //var pubKeys = gbcCipher.loadPubKeys(pubKeyStrs);
          var pubKeys = [key_pair.e2e_key_pub];
          return gbcCipher.encryptArray(fileArr, pubKeys);
        }).then(function(cipherTxtArr) {
          console.log("The intermediate ciphertxt is: ", cipherTxtArr);

          // TESTING TRY THE DECRYPT
          gbcCipher.decryptArray(cipherTxtArr, key_pair.e2e_key_prv, receipt)
          .then(function(clearTxtArr) {
            console.log("The decrypted cleartxt is: ", clearTxtArr);
          });

          var cipherTxtBlob = new Blob([cipherTxtArr.buffer]);
          var encFile = new File([cipherTxtBlob], 'upload.blob.pgp');
          // Change related file settings in flowObj
          deferred.resolve(encFile);
        });
        // TODO delete the file buffer's as soon as possible
        return deferred.promise;
      }
    });
  });
});
