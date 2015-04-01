angular.module('e2e', []).
  factory('whistleblower', function() {
    var wb_names = ['Samuel Shaw',
    'Edmund Dene Morel',
    'Herbert Yardley',
    'Smedley Butler',
    'Jan Karski',
    'John Paul Vann',
    'Peter Buxtun',
    'John White',
    'Daniel Ellsberg',
    'Frank Serpico',
    'Perry Fellwock',
    'Vladimir Bukovsky',
    'W. Mark Felt',
    'Stanley Adams',
    'A. Ernest Fitzgerald',
    'Henri Pezerat',
    'Karen Silkwood',
    'Gregory C. Minor',
    'Richard B. Hubbard', 
    'Dale G. Bridenbaugh',
    'Frank Snepp',
    'Clive Ponting',
    'John Michael Gravitt',
    'Duncan Edmonds',
    'Ingvar Bratt',
    'Cathy Massiter',
    'Ronald J. Goldstein',
    'Mordechai Vanunu',
    'Peter Wright',
    'Roland Gibeault',
    'Douglas D. Keeth',
    'William Schumer',
    'Myron Mehlman',
    'Arnold Gundersen',
    'Joanna Gualtieri',
    'Mark Whitacre',
    'Andr\xe9 Cicolella',
    'William Sanjour',
    'George Galatis',
    'Jeffrey Wigand',
    'Allan Cutler',
    'David Franklin',
    'Michael Ruppert',
    'Nancy Olivieri',
    'Frederic Whitehurst',
    'David Shayler',
    'Christoph Meili',
    'Alan Parkinson',
    'Shiv Chopra',
    'Paul van Buitenen',
    'Marc Hodler',
    'Linda Tripp',
    '\xc1rp\xe1d Pusztai',
    'Harry Markopolos',
    'Youri Bandazhevsky',
    'Marlene Garcia-Esperat',
    'Janet Howard',
    'Tanya Ward Jordan',
    'Joyce E. Megginson',
    'Karen Kwiatkowski',
    'Stefan P. Kruszewski',
    'Guy Pearse',
    'Marsha Coleman-Adebayo',
    'Joseph Nacchio',
    'Pascal Diethelm',
    'Jean-Charles Rielle',
    'Jesselyn Radack',
    'Kathryn Bolkovac',
    'Cynthia Cooper',
    'Sherron Watkins',
    'Coleen Rowley',
    'William Binney',
    'J. Kirke Wiebe',
    'Edward Loomis',
    'Marta Andreasen',
    'Glenn Walp',
    'Steven L. Doran',
    'Sibel Edmonds',
    'Courtland Kelley',
    'Diane Urquhart',
    'Katharine Gun',
    'Robert MacLean',
    'Joseph Wilson',
    'Richard Convertino',
    'Satyendra Dubey',
    'Joe Darby',
    'Neil Patrick Carrick',
    'Hans-Peter Martin',
    'Craig Murray',
    'Gerald W. Brown',
    'David Graham',
    'Samuel Provance',
    'Peter Rost',
    'Richard Levernier',
    'Toni Hoffman',
    'Russ Tice',
    'Maria do Ros\xe0rio Veiga',
    'Thomas Andrews Drake',
    'Bunnatine "Bunny" H. Greenhouse',
    'Brad Birkenfeld',
    'Thomas Tamm',
    'Shawn Carpenter',
    'Rick S. Piltz',
    'Shanmughan Manjunath',
    'Paul Moore',
    'Gary J. Aguirre',
    'Walter DeNino',
    'Marco Pautasso',
    'Mark Klein',
    'Cate Jenkins',
    'Michael G. Winston',
    'Richard M. Bowen III',
    'Adam B. Resnick',
    'Justin Hopson',
    'Sergei Magnitsky',
    'John Kiriakou',
    'Anat Kamm',
    'Rudolf Elmer',
    'Robert J. McCarthy',
    'Herv\xe9 Falciani',
    'Wendell Potter',
    'Cathy Harris',
    'Ramin Pourandarjani',
    'John Kopchinski',
    'Jim Wetta',
    'Joseph Faltaous',
    'Steven Woodward',
    'Jaydeen Vincente',
    'Robert Rudolph',
    'Hector Rosado',
    'Robert Evan Dawitt',
    'William Lofing',
    'Bradly Lutz',
    'Alexander Barankov',
    'Linda Almonte',
    'Chelsea Manning',
    'Bradley Manning',
    'Cheryl D. Eckard',
    'Jim Wetta',
    'Michael Woodford',
    'M. N. Vijayakumar',
    'Blake Percival',
    'Everett Stern',
    'Ted Siska',
    'Vijay Pandhare',
    'Joshua Wilson',
    'Carmen Segarra',
    'Silver Meikar',
    'Antoine Deltour',
    'David P. Weber',
    'Edward Snowden',
    'Laurence do Rego',
    'John Tye',
    'J. Kirk McGill'];

    return {
      generate_key_from_receipt: function(stretched_receipt, cb) {
        function Seed(seed) {
          this.seed = seed;
          function nextBytes(byteArray) {
            for (var n = 0; n < byteArray.length; n++) {
              var buf = new Uint8Array(1);
              buf = this.seed.charCodeAt(n % this.seed.length);
              byteArray[n] = buf;
            }
          }
          this.nextBytes = nextBytes;
        }
        var wb_name = wb_names[Math.floor(Math.random() * wb_names.length)];
        openpgp.generateKeyPair({
          numBits: 2048,
          userId:  wb_name + " <wb@antani.gov>",
          unlocked: true,
          created: new Date(),
          prng: new Seed(stretched_receipt)
        }, function(keyPair){
          console.log("Generated key pair for " + wb_name);
          cb(keyPair);
        });
      }
    }
  }).
  factory('pkdf', function() {
    return {
      // //https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey
      //Chrome: 42
      pbkdf2_deriveAKey: function(password, iterations) {
        var salt = "Pick anything you want. This isn't secret.";
        //var iterations = 1000;
        var hash = "SHA-256";

        // First, create a PBKDF2 "key" containing the password
        window.crypto.subtle.importKey(
          "raw",
          this.pbkdf2_stringToArrayBuffer(password),
          {"name": "PBKDF2"},
          false,
          ["deriveKey"]).
            // Derive a key from the password
            then(function(baseKey){
            return window.crypto.subtle.deriveKey(
              {
              "name": "PBKDF2",
              "salt": this.pbkdf2_stringToArrayBuffer(salt),
              "iterations": iterations,
              "hash": hash
            },
            baseKey,
            {"name": "AES-CBC", "length": 128}, // Key we want
            true,                               // Extrable
            ["encrypt", "decrypt"]              // For new key
            );
          }).
            // Export it so we can display it
            then(function(aesKey) {
            return window.crypto.subtle.exportKey("raw", aesKey);
          }).
            // Return it in hex format
            then(function(keyBytes) {
            var hexKey = this.pbkdf2_arrayBufferToHexString(keyBytes);
            return hexKey;
          }).
            catch(function(err) {
            alert("Key derivation failed: " + err.message);
          });
      },


      // Utility functions
      pbkdf2_stringToArrayBuffer: function(string) {
        var encoder = new TextEncoder("utf-8");
        return encoder.encode(string);
      },

      pbkdf2_arrayBufferToHexString: function(arrayBuffer) {
        var byteArray = new Uint8Array(arrayBuffer);
        var hexString = "";
        var nextHexByte;

        for (var i=0; i<byteArray.byteLength; i++) {
          nextHexByte = byteArray[i].toString(16); // Integer to base 16
          if (nextHexByte.length < 2) {
            nextHexByte = "0" + nextHexByte;
            // Otherwise 10 becomes just a instead of 0a
          }
          hexString += nextHexByte;
        }
        return hexString;
      },

      // rounds must be power of 2
      scrypt_hash: function(password, rounds, scrypt) {
        var utf8_pwd = scrypt.encode_utf8(password);
        var salt = "This is the salt.";

        var bytearray_pwd = scrypt.crypto_scrypt(utf8_pwd, salt, rounds, 8, 1, 16);
        return scrypt.to_hex(bytearray_pwd);
      },

      gl_password: function(password) {
        var scrypt = scrypt_module_factory(33554432);
        var key = this.scrypt_hash(password, 4096, scrypt);
        console.log('gl_password for ', password, ' is ', key);
        return key;
      },

      gl_passphrase: function(passphrase) {
        var scrypt = scrypt_module_factory(33554432);
        var key = this.scrypt_hash(passphrase, 8192, scrypt);
        console.log('gl_passphrase for ', passphrase, ' is ', key);
        return key;
      }
    }
  }).
  factory('pgp', function() {
    return {
      generate_key: function(cb) {
        var email = 'a@b.org';
        var password = 'abc123';

        var k_user_id = email;
        var k_passphrase = password;
        var k_bits = 4096;

        openpgp.config.show_comment = false;
        openpgp.config.show_version = false;

        var key = openpgp.generateKeyPair({
          numBits: k_bits, userId: k_user_id,
          //passphrase: k_passphrase
        }).then(function(keyPair) {
          var zip = new JSZip();
          var folder_name = "globaleaks-keys"
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
