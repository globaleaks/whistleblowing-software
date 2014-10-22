GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', '$modal', 'Admin',
                    'DefaultAppdata', 'passwordWatcher', 'changePasswordWatcher', 'CONSTANTS',
                    function($scope, $rootScope, $location, $route, $http, $modal,
                                                      Admin, DefaultAppdata,
                                                      passwordWatcher,
                                                      changePasswordWatcher,
                                                      CONSTANTS) {

    $scope.email_regexp = CONSTANTS.email_regexp;

    finished = false;

    $scope.login('admin', 'globaleaks', 'admin', function(response){
      $scope.admin = new Admin();
      $scope.receiver = new $scope.admin.new_receiver();
      $scope.receiver.password = GLCrypto.randomString(20);
      $scope.context = $scope.admin.new_context();
      passwordWatcher($scope, 'admin.node.password');
      changePasswordWatcher($scope, "admin.node.old_password",
        "admin.node.password", "admin.node.check_password");
    });

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

  }
]);
