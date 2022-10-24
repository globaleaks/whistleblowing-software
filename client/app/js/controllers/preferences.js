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

    $scope.changePasswordArgs = {};

    $scope.toggleNameEditing = function () {
      $scope.editingName = !$scope.editingName;
    };

    $scope.togglePublicNameEditing = function() {
      $scope.editingPublicName = !$scope.editingPublicName;
    };

    $scope.toggleEmailAddressEditing = function() {
      $scope.editingEmailAddress = !$scope.editingEmailAddress;
    };

    $scope.changePassword = function() {
      return $scope.Utils.runUserOperation("change_password", $scope.changePasswordArgs).then(function() {
        $scope.changePasswordArgs = {};
      });
    };

    $scope.getEncryptionRecoveryKey = function() {
      return $scope.Utils.runUserOperation("get_recovery_key").then(function(data) {
        $scope.resources.preferences.clicked_recovery_key = true;
        $scope.erk = data.data.match(/.{1,4}/g).join("-");
        return $uibModal.open({
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
      // Do not change the value till the configuration is fully applied
      $scope.resources.preferences.two_factor = !$scope.resources.preferences.two_factor;

      if (!$scope.resources.preferences.two_factor) {
        var symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        var array = new Uint32Array(32);

        $window.crypto.getRandomValues(array);

        $scope.totp = {
          "qrcode_string": "",
          "secret": "",
          "edit": false
        };

        for (var i = 0; i < array.length; i++) {
          $scope.totp.secret += symbols[array[i]%symbols.length];
        }

        $scope.$watch("totp.secret", function() {
          $scope.totp.qrcode_string = "otpauth://totp/" + $location.host() + "%20%28" + $scope.resources.preferences.username + "%29?secret=" + $scope.totp.secret;
        });

        $uibModal.open({
          templateUrl: "views/modals/enable_2fa.html",
          controller: "TwoFactorModalCtrl",
          scope: $scope
        });
      } else {
       $scope.Utils.runUserOperation("disable_2fa", {}, true);
      }
    };

    $scope.save = function() {
      if ($scope.resources.preferences.pgp_key_remove) {
        $scope.resources.preferences.pgp_key_public = "";
      }

      return $scope.resources.preferences.$update(function() {
        $scope.reload();
      });
    };

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.resources.preferences.pgp_key_public = txt;
       }, $scope.Utils.displayErrorMsg);
    };
}]).
controller("TwoFactorModalCtrl",
           ["$scope", "$http", "$uibModalInstance", function($scope, $http, $uibModalInstance) {
  $scope.confirm = function(result) {
    return $http({method: "PUT", url: "api/user/operations", data:{
      "operation": "enable_2fa",
      "args": {
        "secret": $scope.totp.secret,
        "token": result
      }
    }}).then(function() {
      $scope.resources.preferences.two_factor = true;
      $uibModalInstance.dismiss("cancel");
    });
  };

  $scope.cancel = function() {
    return $uibModalInstance.dismiss("cancel");
  };
}]);
