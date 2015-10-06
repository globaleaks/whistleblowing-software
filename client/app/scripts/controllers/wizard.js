GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', '$modal', 'Admin',
                    'DefaultAppdata', 'passwordWatcher', 'changePasswordWatcher', 'CONSTANTS',
                    function($scope, $rootScope, $location, $route, $http, $modal,
                                                      Admin, DefaultAppdata,
                                                      passwordWatcher,
                                                      changePasswordWatcher,
                                                      CONSTANTS) {

    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var finished = false;

    $scope.open_modal_allow_unencrypted = function() {
      if (!$scope.admin.node.allow_unencrypted) {
        return;
      }

      var modalInstance = $modal.open({
        templateUrl: 'views/partials/disable_encryption.html',
        controller: 'DisableEncryptionCtrl'
      });

      modalInstance.result.then(function(result){
        $scope.admin.node.allow_unencrypted = result;
      });
    };


    $scope.finish = function() {
      if (!finished) {
        /* configure tor2web admin right based on detected user access */
        $scope.admin.node.tor2web_admin = !$scope.anonymous;

        var admin = {
          'mail_address': $scope.admin_mail_address,
          'old_password': 'globaleaks',
          'password': $scope.admin_password,
        };

        $scope.wizard = {
          'node': $scope.admin.node,
          'admin': admin,
          'receiver': $scope.receiver,
          'context': $scope.context
        };

        $http.post('admin/wizard', $scope.wizard).success(function(response) {
          $rootScope.reload("/admin/landing");
        });
      }
    };

    $scope.$watch("language", function (newVal, oldVal) {
      if (newVal && newVal !== oldVal) {
        $rootScope.language = $scope.language;
      }
    });

    if ($scope.node.wizard_done) {
      /* if the wizard has been already performed redirect to the homepage */
      $location.path('/');
    } else {
      $scope.login('admin', 'globaleaks', function(response){
        $scope.admin = new Admin(function() {
          $scope.receiver = new $scope.admin.new_receiver();
          $scope.receiver.username = 'receiver';
          $scope.receiver.password = ''; // this causes the system to set the default password
                                         // the system will then force the user to change the password
                                         // at first login
          $scope.context = $scope.admin.new_context();
          passwordWatcher($scope, 'admin_password');
          changePasswordWatcher($scope,
                                "globaleaks",
                                "admin_password",
                                "admin_check_password");
        });
      });
    }

  }
]);
