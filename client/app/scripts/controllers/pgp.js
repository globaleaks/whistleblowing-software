
GLClient.controller('PGPConfigCtrl', ['$scope', function($scope){


    $scope.generate_key = function() {
            var email = 'a@b.org';
            var password = 'abc123';

            var k_user_id = email;
            var k_passphrase = password;
            var k_bits = 4096;
            var k_bits = 2048;

            openpgp.config.show_comment = false;
            openpgp.config.show_version = false;

            var key = openpgp.generateKeyPair({ numBits: k_bits,
                                                userId: k_user_id,
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
                    saveAs(content, file_name);

                    if ($scope.receiver) {
                        $scope.receiver.gpg_key_armor = keyPair.publicKeyArmored.trim();
                        $scope.receiver.pgp_key_armor_priv = keyPair.privateKeyArmored.trim();
                        $scope.$apply();
                    } else if ($scope.preferences) {
                        $scope.preferences.gpg_key_armor = keyPair.publicKeyArmored.trim();
                        $scope.preferences.pgp_key_armor_priv = keyPair.privateKeyArmored.trim();
                        $scope.$apply();
                    }

                });

            return true;

    }


}]);

