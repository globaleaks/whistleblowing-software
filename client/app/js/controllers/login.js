GLClient.controller('LoginCtrl', ['$scope', '$location', 'Authentication',
    function($scope, $location, Authentication) {
  $scope.Authentication = Authentication;

  // If already logged in, just go to the landing page.
  // If no longer authenticated on the server (server session expired or some form of malicious hack),
  // the API call will fail, clearing the client session and comming back to this controller without a landing page.
  if ($scope.session !== undefined && $scope.session.auth_landing_page) {
    $location.path($scope.session.auth_landing_page);
  }

  $scope.loginUsername = "";
  $scope.loginPassword = "";

  $scope.simplifiedLogin = !!($location.path() === '/login' && $scope.node.simplified_login);
}]);

GLClient.controller('AutoLoginCtrl', ['Authentication', function(Authentication) {
  function receiveMessage(event) {
    window.removeEventListener('message', this, false);
    Authentication.login('whistleblower', event.data);
  }

  window.addEventListener("message", receiveMessage, false);

  var arr = window.parent.location.href.split("/");
  var parent_domain = arr[0] + "//" + arr[2];
  window.parent.postMessage("Ready", parent_domain);
}]);
