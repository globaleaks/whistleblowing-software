GLClient.controller('PreferencesCtrl', ['$scope', '$rootScope', 'CONSTANTS', 'glbcUserKeyGen',
  function($scope, $rootScope, CONSTANTS, glbcUserKeyGen) {
    if ($scope.session.role === 'receiver') {
      // Receivers currently are the only user that benefit of specialized preferences.
      $scope.tabs = [
        {
          title: "Preferences",
          template: "views/user/preferences/tab1.html"
        },
        {
          title: "Password configuration",
          template: "views/user/preferences/tab2.html"
        },
        {
          title: "Notification settings",
          template: "views/receiver/preferences/tab3.html"
        },
        {
          title:"Encryption settings",
          template:"views/receiver/preferences/tab4.html"
        }
      ];
    } else {
      $scope.tabs = [
        {
          title: "Preferences",
          template: "views/user/preferences/tab1.html"
        },
        {
          title: "Password configuration",
          template: "views/user/preferences/tab2.html"
        },
        {
          title:"Encryption settings",
          template:"views/user/preferences/tab3.html"
        }
      ];
    }

    $scope.navType = 'pills';

    $scope.timezones = CONSTANTS.timezones;
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.inp = {
      old_password: "",
      new_password: "",
    };
    $scope.showKeyGen = false;
    glbcUserKeyGen.setup();

    $scope.pass_next = function() {
      $scope.showKeyGen = true;

      glbcUserKeyGen.noKeyGen();
      glbcUserKeyGen.addPassphrase($scope.inp.old_password, $scope.inp.new_password);
    };

    $scope.pref_save = function() {

      if ($scope.preferences.pgp_key_remove === true) {
        $scope.preferences.pgp_key_public = '';
      }

      if ($scope.preferences.pgp_key_public !== undefined &&
          $scope.preferences.pgp_key_public !== '') {
        $scope.preferences.pgp_key_remove = false;
      }

      $scope.preferences.$update(function() {
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    };
}]);
