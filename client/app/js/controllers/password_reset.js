GLClient.controller('PasswordResetCtrl', ['$scope', '$rootScope', '$location', '$http',
  function($scope, $rootScope, $location, $http) {
  // If already logged in, just go to the landing page.
  if ($scope.session !== undefined && $scope.session.auth_landing_page) {
    $location.path($scope.session.auth_landing_page);
  }

  $scope.resetCredentials = {
    'username': '',
    'mail_address': '',
  };

  var completed = false;

  $scope.passwordResetEnabled = $scope.node.enable_password_reset;

  $scope.complete = function() {
    $http.post('reset/password', $scope.resetCredentials)
    $rootScope.successes.push({message: 'If the specificed account exists, then instructions have been sent to your email.'});
  }
}]);
