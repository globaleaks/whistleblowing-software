GLClient.controller('WizardCtrl', ['$scope', '$location', '$route', '$http', 'Authentication', 'AdminUtils', 'CONSTANTS',
                    function($scope, $location, $route, $http, Authentication, AdminUtils, CONSTANTS) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var completed = false;

    $scope.complete = function() {
      if (completed) {
          return;
      }

      $scope.completed = true;

      $http.post('wizard', $scope.wizard).then(function() {
        $scope.step += 1;
      });
    };

    $scope.goToAdminInterface = function() {
      Authentication.login('admin', $scope.wizard.admin.password, function() {
        $scope.reload("/admin/home");
      });
    };

    if ($scope.node.wizard_done) {
      /* if the wizard has been already performed redirect to the homepage */
      $location.path('/');
    } else {
      var receiver = AdminUtils.new_user();
      receiver.username = 'receiver';
      receiver.password = ''; // this causes the system to set the default password
                              // the system will then force the user to change the password
                              // at first login

      $scope.config_profiles = [
        {
          name:  'default',
          title: 'Default',
          active: true
        },
      ];

      $scope.selectProfile = function(name) {
        angular.forEach($scope.config_profiles, function(p) {
          p.active = p.name === name ? true : false;
          if (p.active) {
            $scope.wizard.profile = p.name;
          }
        });
      };

      var context = AdminUtils.new_context();
      context.questionnaire_id = $scope.node.default_questionnaire;

      $scope.wizard = {
        'node': {},
        'admin': {
          'mail_address': '',
          'password': ''
        },
        'receiver': receiver,
        'context': context,
        'profile': 'default'
      };
    }
  }
]);
