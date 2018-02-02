    GLClient.controller('SignupCtrl', ['$scope', '$location', '$route', '$http', 'Authentication', 'CONSTANTS',
                    function($scope, $location, $route, $http, Authentication, CONSTANTS) {

  $scope.email_regexp = CONSTANTS.email_regexp;

  $scope.hostname = $location.search().hostname || '';

  $scope.step = 1;
  $scope.signup = {
    'subdomain': '',
    'name': '',
    'surname': '',
    'email': '',
    'use_case': '',
    'use_case_other': ''
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
controller('SignupActivationCtrl', ['$scope', '$location', '$route', '$http', '$window',
                    function($scope, $location, $route, $http, $window) {
  var token = $location.search().token;
  $scope.login_url = '';

  if (token) {
    $http.get('signup/' + token).then(function(response) {
      $scope.data = response.data;
    });
  }

  $scope.goToAdminInterface = function() {
    $window.open($scope.data.admin_login_url, '_blank');
  };

  $scope.goToRecipientInterface = function() {
    $window.open($scope.data.recipient_login_url, '_blank');
  };
}]);
