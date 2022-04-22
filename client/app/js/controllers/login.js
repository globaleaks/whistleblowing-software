GL.controller("LoginCtrl", ["$scope", "$location", function($scope, $location) {
  $scope.loginData = {
    loginUsername: "",
    loginPassword: "",
    loginAuthCode: ""
  };

  // If already logged in, just go to the landing page.
  if (typeof $scope.Authentication.session !== "undefined" && $scope.Authentication.session.homepage) {
    $location.path($scope.Authentication.session.homepage);
  }

  if ($location.path() === "/login" && $scope.public.node.simplified_login) {
    $scope.login_template = "views/login/simplified.html";
  } else {
    $scope.login_template = "views/login/default.html";
  }

  var token = $location.search().token;
  if (token) {
    $scope.Authentication.login(0, "", "", "", token);
  }
}]);
