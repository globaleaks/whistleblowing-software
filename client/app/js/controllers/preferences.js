GLClient.controller('PreferencesCtrl', ['$scope', '$rootScope', 'Utils', 'CONSTANTS',
  function($scope, $rootScope, Utils, CONSTANTS) {
    $scope.tabs = [
      {
        title: "Preferences",
        template: "views/preferences/tab1.html"
      },
      {
        title: "Password",
        template: "views/preferences/tab2.html"
      }
    ];

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
