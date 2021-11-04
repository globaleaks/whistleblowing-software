GL.controller("PreferencesCtrl", ["$scope", "$q", "$http", "$location", "$window", "$uibModal",
  function($scope, $q, $http, $location, $window, $uibModal) {
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

    $scope.editingName = false;
    $scope.editingPublicName = false;
    $scope.showEncryptionKey = false;

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
          templateUrl: "views/modals/encryption_recovery_key.html",
          controller: "ConfirmableModalCtrl",
          scope: $scope,
          resolve: {
            arg: null,
            confirmFun: null,
            cancelFun: null
          }
        });
      });
    };

    $scope.toggle2FA = function() {
      var symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
      var array = new Uint32Array(32);

      $window.crypto.getRandomValues(array);

      $scope.totp = {
        'qrcode_string': "",
        'secret': "",
        'edit': false
      };

      for (var i = 0; i < array.length; i++) {
        $scope.totp.secret += symbols[array[i]%symbols.length];
      }

      $scope.$watch("totp.secret", function(new_val, old_val) {
        $scope.totp.qrcode_string = "otpauth://totp/" + $location.host() + "%20%28" + $scope.preferences.username + "%29?secret=" + $scope.totp.secret;
      });

      if ($scope.preferences.two_factor_enable) {
        $scope.preferences.two_factor_enable = false;

        $uibModal.open({
          templateUrl: "views/modals/enable_2fa.html",
          controller: "TwoFactorModalCtrl",
          scope: $scope
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
}]).
controller("EmailValidationCtrl", [
  function() {

}]).
controller("TwoFactorModalCtrl",
           ["$scope", "$window", "$http", "$location", "$uibModalInstance", function($scope, $window, $http, $location, $uibModalInstance) {
  $scope.confirm = function(result) {
    return $http({method: "PUT", url: "api/user/operations", data:{
      "operation": "enable_2fa",
      "args": {
        "secret": $scope.totp.secret,
        "token": result
      }
    }}).then(function() {
      $scope.preferences.two_factor_enable = true;
      $uibModalInstance.dismiss("cancel");
    });
  };

  $scope.cancel = function(result) {
    return $uibModalInstance.dismiss("cancel");
  };
}]);
