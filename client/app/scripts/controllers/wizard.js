GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', '$modal', 'Admin',
                    'Node', 'DefaultAppdata', 'passwordWatcher', 'changePasswordWatcher', 'CONSTANTS',
                    function($scope, $rootScope, $location, $route, $http, $modal,
                                                      Admin, Node, DefaultAppdata,
                                                      passwordWatcher,
                                                      changePasswordWatcher,
                                                      CONSTANTS) {

    $scope.email_regexp = CONSTANTS.email_regexp;

    finished = false;

    $scope.open_modal_allow_unencrypted = function() {
      if ($scope.admin.node.allow_unencrypted)
        return;
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
        finished = true;
        DefaultAppdata.get(function(res) {
          $scope.admin.node.old_password = 'globaleaks';

          /* configure tor2web admin right based on detected user access */
          $scope.admin.node.tor2web_admin = !$scope.anonymous;
          console.log($scope.admin.node);

          $scope.wizard = {
            'node': $scope.admin.node,
            'appdata': res,
            'receiver': $scope.receiver,
            'context': $scope.context
          };

          $http.post('/admin/wizard', $scope.wizard).success(function(response) {
            /* needed in order to reload node variables */
            $rootScope.$broadcast("REFRESH");
            $location.path("/admin/landing");
          });
        });
      }
    };

    $scope.$watch("language", function (newVal, oldVal) {
      if (newVal && newVal !== oldVal) {
        $rootScope.language = $scope.language;
      }
    });

    Node.get(function (node) {
      $scope.node = node;
      if ($scope.node.wizard_done) {
        /* if the wizard has been already performed redirect to the homepage */
        $location.path('/');
      } else {
        $scope.login('admin', 'globaleaks', 'admin', function(response){
          $scope.admin = new Admin();
          $scope.receiver = new $scope.admin.new_receiver();
          $scope.receiver.password = ''; // this causes the system to set the default password
                                         // the system will then force the user to change the password
                                         // at first login
          $scope.context = $scope.admin.new_context();
          passwordWatcher($scope, 'admin.node.password');
          changePasswordWatcher($scope, "admin.node.old_password",
            "admin.node.password", "admin.node.check_password");
        });
      }
    });

  }
]);
