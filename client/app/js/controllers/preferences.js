GL.controller("PreferencesCtrl", ["$scope", "$q", "$http", "$uibModal", "$http", "CONSTANTS",
  function($scope, $q, $http, $uibModal, CONSTANTS) {
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

    $scope.vars = {};

    $scope.email_regexp = CONSTANTS.email_regexp;
    $scope.editingName = false;
    $scope.editingPublicName = false;
    $scope.showEncryptionKey = false;
    $scope.qrcode_string = "";

    $scope.toggleNameEditing = function () {
      $scope.editingName = !$scope.editingName;
    };

    $scope.togglePublicNameEditing = function() {
      $scope.editingPublicName = !$scope.editingPublicName;
    };

    $scope.toggleEmailAddressEditing = function() {
      $scope.editingEmailAddress = !$scope.editingEmailAddress;
    };

    $scope.getEncryptionRecoveryKey = function() {
      return $http({method: "PUT", url: "api/user/operations", data:{
        "operation": "get_recovery_key",
        "args": {}
      }}).then(function(data){
	$scope.preferences.clicked_recovery_key = true;
        $scope.erk = data.data.match(/.{1,4}/g).join("-");
        $uibModal.open({
          templateUrl: "views/partials/encryption_recovery_key.html",
          controller: "ConfirmableModalCtrl",
          size: "lg",
          scope: $scope,
          backdrop: "static",
          keyboard: false,
          resolve: {
            arg: null,
            confirmFun: null,
            cancelFun: null
          }
        });
      });
    };

    $scope.toggle2FA = function() {
      if ($scope.preferences.two_factor_enable) {
        $scope.preferences.two_factor_enable = false;

        return $http({method: "PUT", url: "api/user/operations", data:{
          "operation": "enable_2fa_step1",
          "args": {}
        }}).then(function(data){
          $scope.two_factor_secret = data.data;
          $scope.qrcode_string = "otpauth://totp/GlobaLeaks?secret=" + $scope.two_factor_secret;

          $scope.Utils.openConfirmableModalDialog("views/partials/enable_2fa_modal.html", {}, $scope).then(function (result) {
            return $http({method: "PUT", url: "api/user/operations", data:{
              "operation": "enable_2fa_step2",
              "args": {
                "value": result
              }
            }}).then(function() {
              $scope.preferences.two_factor_enable = true;
            });
          });
        });
      } else {
        return $http({method: "PUT", url: "api/user/operations", data:{
          "operation": "disable_2fa",
          "args": {}
        }}).then(function() {
          $scope.preferences.two_factor_enable = false;
        });
      }
    };

    $scope.save = function() {
      if ($scope.preferences.pgp_key_remove) {
        $scope.preferences.pgp_key_public = "";
      }

      return $scope.preferences.$update(function() {
        $scope.reload();
      });
    };

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.preferences.pgp_key_public = txt;
       }, $scope.Utils.displayErrorMsg);
    };
}]);

GL.controller("EmailValidationCtrl", [
  function() {

}]);
