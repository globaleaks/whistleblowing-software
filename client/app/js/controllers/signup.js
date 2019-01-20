    GLClient.controller("SignupCtrl", ["$scope", "$location", "$route", "$http", "Authentication", "CONSTANTS", "DATA_COUNTRIES_ITALY_REGIONS", "DATA_COUNTRIES_ITALY_PROVINCES", "DATA_COUNTRIES_ITALY_CITIES",
                    function($scope, $location, $route, $http, Authentication, CONSTANTS, DATA_COUNTRIES_ITALY_REGIONS, DATA_COUNTRIES_ITALY_PROVINCES, DATA_COUNTRIES_ITALY_CITIES) {
  if ($scope.node.mode === "whistleblowing.it") {
    $scope.data_countries_italy_regions = DATA_COUNTRIES_ITALY_REGIONS.query();
    $scope.data_countries_italy_provinces = DATA_COUNTRIES_ITALY_PROVINCES.query();
    $scope.data_countries_italy_cities = DATA_COUNTRIES_ITALY_CITIES.query();
  }

  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.phonenumber_regexp = CONSTANTS.phonenumber_regexp;

  $scope.hostname = $location.search().hostname || "";

  $scope.step = 1;
  $scope.signup = {
    "subdomain": "",
    "name": "",
    "surname": "",
    "role": "",
    "email": "",
    "phone": "",
    "use_case": "",
    "use_case_other": "",
    "organization_name": "",
    "organization_type": "",
    "organization_location1": "",
    "organization_location2": "",
    "organization_location3": "",
    "organization_location4": "",
    "organization_number_employees": "",
    "organization_number_users": "",
    "organization_site": "",
    "hear_channel": "",
    "tos1": false,
    "tos2": false
  };

  var completed = false;

  $scope.updateSubdomain = function() {
    $scope.signup.subdomain = $scope.signup.organization_name.replace(/[^\w]/gi, "").toLowerCase();
  }

  $scope.complete = function() {
    if (completed) {
        return;
    }

    completed = true;

    $http.post("signup", $scope.signup).then(function() {
      $scope.step += 1;
    });
  };
}]).
controller("SignupActivationCtrl", ["$scope", "$location", "$http",
                    function($scope, $location, $http) {
  var token = $location.search().token;

  if (token) {
    $http.get("signup/" + token);
  }
}]);
