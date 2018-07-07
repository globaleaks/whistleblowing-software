    GLClient.controller('SignupCtrl', ['$scope', '$location', '$route', '$http', 'Authentication', 'CONSTANTS',
                    function($scope, $location, $route, $http, Authentication, CONSTANTS) {
  $scope.email_regexp = CONSTANTS.email_regexp;

  $scope.hostname = $location.search().hostname || '';

  $scope.step = 1;
  $scope.signup = {
    'subdomain': '',
    'name': '',
    'surname': '',
    'role': '',
    'phone': '',
    'email': '',
    'secondary_email': '',
    'use_case': '',
    'use_case_other': '',
    'organization_name': '',
    'organization_type': '',
    'organization_location1': '',
    'organization_location2': '',
    'organization_location3': '',
    'organization_location4': '',
    'organization_number_employees': '',
    'organization_number_users': '',
    'hear_channel': '',
    'hear_channel_other': '',
    'tos1': false,
    'tos2': false
  };

  var completed = false;

  $scope.complete = function() {
    if (completed) {
        return;
    }

    completed = true;

    $http.post('signup', $scope.signup).then(function() {
      $scope.step += 1;
    });
  };
}]).
controller('SignupActivationCtrl', ['$scope', '$location', '$http',
                    function($scope, $location, $http) {
  var token = $location.search().token;

  if (token) {
    $http.get('signup/' + token).then(function(response) {
      $scope.data = response.data;
    });
  }
}]);
