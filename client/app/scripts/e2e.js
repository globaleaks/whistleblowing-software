angular.module('e2e', []).
  factory('pkdf', function() {
    return {
      // rounds must be power of 2
      scrypt_hash: function(password, rounds, scrypt) {
        var utf8_pwd = scrypt.encode_utf8(password);
        var salt = "This is the salt.";

        var bytearray_pwd = scrypt.crypto_scrypt(utf8_pwd, salt, rounds, 8, 1, 16);
        return scrypt.to_hex(bytearray_pwd);
      },
      
      gl_receipt: function() {
        var receipt = "",
          random = openpgp.crypto.random,
          scrypt = scrypt_module_factory(33554432),
          stretched;

        for (var i=0; i<16; i++) {
          receipt += random.getSecureRandom(0, 9);
        }
        var utf8_pwd = scrypt.encode_utf8(receipt);
        var salt = "This is the salt.";
        stretched = scrypt.crypto_scrypt(utf8_pwd, salt, 4096, 8, 1, 128);
        console.log('gl_receipt ', receipt);
        return {
          value: receipt,
          stretched: stretched
        }
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
  factory('whistleblower', function() {
    var wb_names = [
      'Samuel Shaw',
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
      'J. Kirk McGill'
    ];
    return {
      names: wb_names,
      generate_key_from_receipt: function(receipt, cb) {
        console.log('generate_key_from_receipt ', receipt, ' ', typeof(receipt));
        function Seed() {
          var self = this,
            scrypt = scrypt_module_factory(33554432),
            utf8_pwd = scrypt.encode_utf8(receipt),
            salt = "This is the salt.";
          self.offset = 0;
          self.seed = scrypt.crypto_scrypt(utf8_pwd, salt, 4096,
                                           8, 1, 128 * 2);
          function nextBytes(byteArray) {
            for (var n = 0; n < byteArray.length; n++) {
              byteArray[n] = self.seed[self.offset % self.seed.length];
              self.offset += 1;
            }
          }
          this.nextBytes = nextBytes;
        }
        var wb_name = wb_names[Math.floor(Math.random() * wb_names.length)];
        openpgp.generateKeyPair({
          numBits: 2048,
          userId: "wb@antani.gov",
          unlocked: true,
          prng: new Seed()
        }).then(function(keyPair){
          keyPair.key.primaryKey.created = new Date(42);
          keyPair.key.subKeys[0].subKey.created = new Date(42);
          console.log("Generated key pair for " + wb_name);
          console.log(keyPair.key.primaryKey.fingerprint);
          cb(keyPair);
        });
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
