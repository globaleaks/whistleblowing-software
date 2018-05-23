GLClient.controller('PreferencesCtrl', ['$scope', '$q', '$rootScope', 'Utils', 'CONSTANTS',
  function($scope, $q, $rootScope, Utils, CONSTANTS) {
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
    $scope.editingName = false;
    $scope.editingEmail = false;

    $scope.toggleNameEditing = function () {
      $scope.editingName = $scope.editingName ^ 1;
    };

    $scope.toggleEmailAddressEditing = function() {
      $scope.editingEmailAddress = $scope.editingEmailAddress ^ 1;
    };

    $scope.save = function() {
      if ($scope.preferences.pgp_key_remove) {
        $scope.preferences.pgp_key_public = '';
      }

      $scope.preferences.$update(function() {
        $rootScope.successes.push({message: 'Updated your preferences!'});
        $scope.reload()
      });
    };

    $scope.loadPublicKeyFile = function(file) {
      Utils.readFileAsText(file).then(function(txt) {
        $scope.preferences.pgp_key_public = txt;
       }, Utils.displayErrorMsg);
    };
}]);

GLClient.controller('EmailValidationCtrl', [
  function() {

}]);
