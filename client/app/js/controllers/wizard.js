GLClient.controller('WizardCtrl', ['$scope', '$location', '$route', '$http', 'Authentication', 'AdminUtils', 'AdminNodeResource', 'AdminTLSConfigResource', 'CONSTANTS',
                    function($scope, $location, $route, $http, Authentication, AdminUtils, AdminNodeResource, AdminTLSConfigResource, CONSTANTS) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;


    var submitReq = false;

    $scope.submitWizard = function() {
      if (!submitReq) {
        submitReq = true;
        $http.post('wizard', $scope.wizard).then(function() {
          Authentication.login('admin', $scope.wizard.admin.password, function() {
            $scope.admin = {
              node: AdminNodeResource.get(),
            };
            $scope.admin.node.$promise.then(function() {
              $scope.https_redirect_modal = 'views/wizard/https_success_modal.html';
              $scope.https_redirect_path = '/#/admin/home';
              $scope.https_manual_enabled = false;
              $scope.step = $scope.step + 1;
            });
          });
        });
      }
    };

    $scope.skipHTTPS = function() {
      (new AdminTLSConfigResource()).$delete().then(function() {
        $scope.reload("/admin/home");
      });
    }

    $scope.finish = function() {
      $scope.reload("/admin/home");
    }

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
          title: 'Default profile',
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
