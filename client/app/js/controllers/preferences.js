GLClient.controller("PreferencesCtrl", ["$scope", "$rootScope", "$q", "$http", "$uibModal", "$http", "CONSTANTS",
  function($scope, $rootScope, $q, $http, $uibModal, CONSTANTS) {
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
    $scope.showEncryptionKey = false;

    $scope.toggleNameEditing = function () {
      $scope.editingName = !$scope.editingName;
    };

    $scope.toggleEmailAddressEditing = function() {
      $scope.editingEmailAddress = !$scope.editingEmailAddress;
    };

    $scope.getEncryptionRecoveryKey = function() {
      return $http({method: "PUT", url: "user/operations", data:{
        "operation": 'get_recovery_key',
        "args": {}
      }}).then(function(data){
        $scope.erk = data.data.match(/.{1,4}/g).join("-");
        $uibModal.open({
          templateUrl: "views/partials/encryption_recovery_key.html",
          controller: 'ModalCtrl',
          size: "lg",
          scope: $scope,
          backdrop: "static",
          keyboard: false
        });
      });
    }

    $scope.save = function() {
      if ($scope.preferences.pgp_key_remove) {
        $scope.preferences.pgp_key_public = "";
      }

      $scope.preferences.$update(function() {
        $rootScope.successes.push({message: "Updated your preferences!"});
        $scope.reload();
      });
    };

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.preferences.pgp_key_public = txt;
       }, $scope.Utils.displayErrorMsg);
    };
}]);

GLClient.controller("EmailValidationCtrl", [
  function() {

}]);
