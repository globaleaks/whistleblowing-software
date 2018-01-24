GLClient.controller('PreferencesCtrl', ['$scope', '$rootScope', 'Utils', 'CONSTANTS',
  function($scope, $rootScope, Utils, CONSTANTS) {
    if ($scope.session.role === 'receiver') {
      // Receivers currently are the only user that benefit of specialized preferences.
      $scope.tabs = [
        {
          title: "Preferences",
          template: "views/receiver/preferences/tab1.html"
        },
        {
          title: "Password configuration",
          template: "views/receiver/preferences/tab2.html"
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

    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.save = function() {
      if ($scope.preferences.pgp_key_remove) {
        $scope.preferences.pgp_key_public = '';
      }

      $scope.preferences.$update(function() {
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    };

    $scope.loadPublicKeyFile = function(file) {
      Utils.readFileAsText(file).then(function(txt) {
        $scope.preferences.pgp_key_public = txt;
       }, Utils.displayErrorMsg);
    };
}]);
