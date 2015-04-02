GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);

GLClient.controller('ReceiverFirstLoginCtrl', ['$scope', '$rootScope', '$location', 'ReceiverPreferences', 'changePasswordWatcher', 'pkdf',
  function($scope, $rootScope, $location, ReceiverPreferences, changePasswordWatcher, pkdf) {

    $scope.preferences = ReceiverPreferences.get();

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function () {
      $scope.preferences.pgp_key_remove = false;

      var new_password = pkdf.gl_password($scope.preferences.password);
      var new_passphrase = pkdf.gl_passphrase($scope.preferences.password);
      console.log('first login password ', $scope.preferences.password, ' ', new_password);
      console.log('first login passphrase ', new_passphrase);

      //$scope.preferences.old_password = old_pwd;
      $scope.preferences.password = new_password;
      $scope.preferences.check_password = new_password;

      //TODO: add e-mail
      var k_user_id = $scope.preferences.email;
      var k_user_id = 'fake@email.com';
      var k_passphrase = new_passphrase;
      var k_bits = 2048;

      openpgp.config.show_version = false;
      openpgp.config.show_comment = false;

      key = openpgp.generateKeyPair({   numBits: k_bits,
                                        userId: k_user_id,
                                        passphrase: k_passphrase }).then(function(keyPair) {

            $scope.preferences.pgp_e2e_public = keyPair.publicKeyArmored;
            $scope.preferences.pgp_e2e_private = keyPair.privateKeyArmored;

            $scope.preferences.$update(function () {
                if (!$rootScope.successes) {
                    $rootScope.successes = [];
                }
                $rootScope.successes.push({message: 'Updated your password!'});
                $location.path("/receiver/tips");
            });
      });

    };

}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'ReceiverPreferences', 'changePasswordWatcher', 'CONSTANTS', 'pkdf',
  function($scope, $rootScope, ReceiverPreferences, changePasswordWatcher, CONSTANTS, pkdf) {

    $scope.tabs = [
      {
        title: "Password Configuration",
        template: "views/receiver/preferences/tab1.html",
        ctrl: TabCtrl
      },
      {
        title: "Notification Settings",
        template: "views/receiver/preferences/tab2.html",
        ctrl: TabCtrl
      },
      {
        title:"Encryption Settings",
        template:"views/receiver/preferences/tab3.html",
        ctrl: TabCtrl
      }
    ];

    $scope.navType = 'pills';

    $scope.timezones = CONSTANTS.timezones;
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.preferences = ReceiverPreferences.get();

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function () {

      if ($scope.preferences.pgp_key_remove == undefined) {
        $scope.preferences.pgp_key_remove = false;
      }
      if ($scope.preferences.pgp_key_public == undefined) {
        $scope.preferences.pgp_key_public = '';
      }

      var new_password = pkdf.gl_password($scope.preferences.password);
      var old_password = pkdf.gl_password($scope.preferences.old_password);
      var new_passphrase = pkdf.gl_passphrase($scope.preferences.password);
      console.log('update login password ', $scope.preferences.password, ' ', new_password);
      console.log('old login password ', $scope.preferences.old_password, ' ', old_password);
      console.log('update passphrase ', new_passphrase);

      if (!$scope.preferences.pgp_e2e_public) {

            //TODO: receiver email if present
            var k_user_id = $scope.preferences.email;
            var k_user_id = 'fake@email.com';
            var k_passphrase = new_passphrase;
            var k_bits = 2048;

            openpgp.config.show_version = false;
            openpgp.config.show_comment = false;

            key = openpgp.generateKeyPair({ numBits: k_bits,
                                            userId: k_user_id,
                                            passphrase: k_passphrase }).then(function(keyPair) {

                $scope.preferences.pgp_e2e_public = keyPair.publicKeyArmored;
                $scope.preferences.pgp_e2e_private = keyPair.privateKeyArmored;
                $scope.preferences.old_password = old_password;
                $scope.preferences.password = new_password;
                $scope.preferences.check_password = new_password;

                $scope.preferences.$update(function () {
                    if (!$rootScope.successes) {
                        $rootScope.successes = [];
                    }
                    $rootScope.successes.push({message: 'Updated your password!'});
                });

            });

      } else {
            var old_passphrase = pkdf.gl_passphrase($scope.preferences.old_password);
            console.log('update old passphrase ', $scope.preferences.old_password, ' ', old_passphrase);

            try {
                privKey = openpgp.key.readArmored( $scope.preferences.pgp_e2e_private ).keys[0];
            } catch (e) {
                throw new Error('Importing key failed. Parsing error!');
            }
            if (!privKey.decrypt( old_passphrase )) {
                throw new Error('Old passphrase incorrect!');
            }
            try {
                packets = privKey.getAllKeyPackets();
                for (var i = 0; i < packets.length; i++) {
                    packets[i].encrypt( new_passphrase );
                }
                newKeyArmored = privKey.armor();
            } catch (e) {
                throw new Error('Setting new passphrase failed!');
            }
            if (!privKey.decrypt( new_passphrase )) {
                throw new Error('Decrypting key with new passphrase failed!');
            }
            $scope.preferences.pgp_e2e_private = newKeyArmored;
            $scope.preferences.old_password = old_password;
            $scope.preferences.password = new_password;
            $scope.preferences.check_password = new_password;

            $scope.preferences.$update(function () {
                if (!$rootScope.successes) {
                    $rootScope.successes = [];
                }
                $rootScope.successes.push({message: 'Updated your password!'});
            });

      }

    };

    $scope.pref_save = function() {

      $scope.preferences.password = '';
      $scope.preferences.old_password = '';

      if ($scope.preferences.pgp_key_remove == true) {
        $scope.preferences.pgp_key_public = '';
      }

      if ($scope.preferences.pgp_key_public !== undefined &&
          $scope.preferences.pgp_key_public != '') {
        $scope.preferences.pgp_key_remove = false;
      }

      $scope.preferences.$update(function(){

        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    }

}]);

GLClient.controller('ReceiverTipsCtrl', ['$scope', 'ReceiverTips',
  function($scope, ReceiverTips) {
  $scope.tips = ReceiverTips.query();
}]);
