GLClient.controller('LoginCtrl', ['$scope', '$location', 'Authentication', function($scope, $location, Authentication) {
  // If already logged in, just go to the landing page.
  // If no longer authenticated on the server (server session expired or some form of malicious hack),
  // the API call will fail, clearing the client session and comming back to this controller without a landing page.
  if (Authentication.auth_landing_page) {
    $location.path(Authentication.auth_landing_page);
  }

  $scope.loginUsername = "";
  $scope.loginPassword = "";

  if ($location.path() === '/login' && $scope.node.simplified_login) {
    $scope.simplifiedLogin = true;
  } else {
    $scope.simplifiedLogin = false;
  }
}]);
