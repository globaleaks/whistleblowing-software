GL.controller("SignupCtrl", ["$scope", "$location", "$route", "$http",
              function($scope, $location, $route, $http) {
  /* if the signup module is not enabled */
  if (!$scope.public.node.enable_signup) {
    $location.path("/");
    return;
  }

  $scope.hostname = "";

  $scope.step = 1;
  $scope.signup = {
    "subdomain": "",
    "name": "",
    "surname": "",
    "role": "",
    "email": "",
    "phone": "",
    "organization_name": "",
    "organization_type": "",
    "organization_tax_code": "",
    "organization_vat_code": "",
    "organization_location": "",
    "tos1": false,
    "tos2": false
  };

  var completed = false;

  $scope.updateSubdomain = function() {
    $scope.signup.subdomain = "";
    if ($scope.signup.organization_name) {
      $scope.signup.subdomain = $scope.signup.organization_name.replace(/[^\w]/gi, "");
      $scope.signup.subdomain = $scope.signup.subdomain.toLowerCase();
      $scope.signup.subdomain = $scope.signup.subdomain.replace(/[^a-z0-9-]/g,"");
      $scope.signup.subdomain = $scope.signup.subdomain.substring(0, 60);
    }
  };

  $scope.complete = function() {
    if (completed) {
        return;
    }

    completed = true;

    $http.post("api/signup", $scope.signup).then(function() {
      $scope.step += 1;
    });
  };
}]).
controller("SignupActivationCtrl", ["$scope", "$http", "$location",
                    function($scope, $http, $location) {
  var token = $location.search().token;
  if (token) {
    $http.post("api/signup/" + token);
  }
}]);
