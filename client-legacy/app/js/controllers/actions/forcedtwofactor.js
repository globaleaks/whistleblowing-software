GL.controller("EnableTwoFactorAuthCtrl", ["$scope", "$http", "$location", "$window",
  function($scope, $http, $location, $window) {
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

    $scope.enable2FA = function(token) {
      return $http({method: "PUT", url: "api/user/operations", data:{
        "operation": "enable_2fa",
        "args": {
          "secret": $scope.totp.secret,
          "token": token
        }
      }}).then(function() {
	$scope.resources.preferences.two_factor = true;
        $scope.Authentication.session.two_factor = true;
        $location.path($scope.Authentication.session.homepage);
      });
    };
}]);
