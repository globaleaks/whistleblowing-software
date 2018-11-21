GLClient.controller('PreferencesCtrl', ['$scope', '$q', '$rootScope', 'CONSTANTS',
  function($scope, $q, $rootScope, CONSTANTS) {
    $scope.tabs = [
      {
        title: "Preferences",
        template: "views/partials/preferences/tab1.html"
      },
      {
        title: "Password",
        template: "views/partials/preferences/tab2.html"
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
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.preferences.pgp_key_public = txt;
       }, $scope.Utils.displayErrorMsg);
    };
}]);

GLClient.controller('EmailValidationCtrl', [
  function() {

}]);
