/*global QRious*/

GLClient.controller("EnableTwoFactorAuthCtrl", ["$scope", "$http", "$location",
  function($scope, $http, $location) {
    $scope.vars = {};

    $http({method: "PUT", url: "user/operations", data:{
      "operation": "enable_2fa_step1",
      "args": {}
    }}).then(function(data){
      $scope.two_factor_secret = data.data;
      var qr = new QRious({
        value: "otpauth://totp/GlobaLeaks?secret=" + $scope.two_factor_secret,
        size: "240"
      });

      $scope.two_factor_qrcode = qr.toDataURL();
    });

    $scope.enable2FA = function() {
      return $http({
        method: "PUT",
        url: "user/operations",
        data: {
          "operation": "enable_2fa_step2",
          "args": {
            "value": $scope.vars.token_2fa
          }
	}
      }).then(function() {
        $scope.Authentication.session.two_factor = true;
        $scope.preferences.two_factor_enable = true;
        $location.path($scope.Authentication.session.auth_landing_page);
      });
    };
}]);
