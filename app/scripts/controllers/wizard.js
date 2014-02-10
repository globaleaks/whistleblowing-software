GLClient.controller('WizardCtrl', ['$scope', '$location', '$http', 'Admin',
                    'DefaultFields', 'passwordWatcher',
                    'changePasswordWatcher', function($scope, $location, $http,
                                                      Admin, DefaultFields,
                                                      passwordWatcher,
                                                      changePasswordWatcher) {

    if ($scope.role != 'admin') {
      $scope.login('admin', 'globaleaks', 'admin', function(response){
        $scope.admin = new Admin();
        $scope.receiver = new $scope.admin.new_receiver();
        $scope.receiver.password = GLCrypto.randomString(20);
        $scope.context = $scope.admin.new_context();
        passwordWatcher($scope, 'admin.node.password');
        changePasswordWatcher($scope, "admin.node.old_password",
          "admin.node.password", "admin.node.check_password");

      });
    }

    $scope.finish = function() {
      DefaultFields.get(function(res) {
        $scope.admin.node.old_password = 'globaleaks';
        $scope.wizard = {
          'node': $scope.admin.node,
          'fields': res,
          'receiver': $scope.receiver,
          'context': $scope.context
        };

        $http.post('/admin/wizard', $scope.wizard).success(function(response) {
          $location.path("/admin/landing")
        });
      });
    };

  }
]);
