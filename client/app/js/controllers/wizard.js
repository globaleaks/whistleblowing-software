GLClient.controller('WizardCtrl', ['$scope', '$location', '$route', '$http', 'Authentication', 'CONSTANTS',
                    function($scope, $location, $route, $http, Authentication, CONSTANTS) {
  /* if the wizard has been already performed redirect to the homepage */
  if ($scope.node.wizard_done) {
    $location.path('/');
    return;
  }

  $scope.email_regexp = CONSTANTS.email_regexp;

  $scope.step = 1;

  var completed = false;

  $scope.complete = function() {
    if (completed) {
        return;
    }

    completed = true;

    $http.post('wizard', $scope.wizard).then(function() {
      $scope.step += 1;
    });
  };

  $scope.goToAdminInterface = function() {
    Authentication.login('admin', $scope.wizard.admin_password, null, function() {
      $scope.reload("/admin/home");
    });
  };

  $scope.config_profiles = [
    {
      name:  'default',
      title: 'Default',
      active: true
    }
  ];

  $scope.selectProfile = function(name) {
    angular.forEach($scope.config_profiles, function(p) {
      p.active = p.name === name ? true : false;
      if (p.active) {
        $scope.wizard.profile = p.name;
      }
    });
  };

  $scope.wizard = {
    'node_name': '',
    'admin_password': '',
    'admin_name': '',
    'admin_mail_address': '',
    'receiver_name': '',
    'receiver_mail_address': '',
    'profile': 'default',
    'enable_developers_exception_notification': true
  };
}]);
