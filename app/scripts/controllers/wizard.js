GLClient.controller('WizardCtrl', ['$scope', '$location', '$http', 'Admin',
                    'DefaultFields', 'passwordWatcher',
                    'changePasswordWatcher', function($scope, $location, $http,
                                                      Admin, DefaultFields,
                                                      passwordWatcher,
                                                      changePasswordWatcher) {
    
    $scope.receiver = {'password': GLCrypto.randomString(20)};
    $scope.context = {};

    $scope.login('admin', 'globaleaks', 'admin', function(response){
      $scope.admin = new Admin();
      passwordWatcher($scope, 'admin.node.password');
      changePasswordWatcher($scope, "admin.node.old_password",
        "admin.node.password", "admin.node.check_password");

    });

    $scope.finish = function() {
      DefaultFields.get(function(res) {
        $http.post('/admin/wizard/fields', res).success(function(response) {
          var receiver = new $scope.admin.receiver;

          receiver.name = $scope.receiver.name;
          receiver.password = $scope.receiver.password;
          receiver.mail_address = $scope.receiver.email;

          // Under here go default settings
          receiver.contexts =  [];
          receiver.description = "";
          receiver.can_delete_submission = false;
          receiver.postpone_superpower = false;
          receiver.receiver_level = 1;
          receiver.tags = [];
          receiver.tip_notification = true;
          receiver.file_notification = true;
          receiver.comment_notification = true;
          receiver.message_notification = true;
          receiver.gpg_key_info = '';
          receiver.gpg_key_fingerprint = '';
          receiver.gpg_key_remove = false;
          receiver.gpg_key_armor = '';
          receiver.gpg_key_status = 'ignored';
          receiver.gpg_enable_notification = false;
          receiver.gpg_enable_files = false;
          receiver.presentation_order = 0;
          receiver.$save(function(added_receiver){
            $scope.admin.create_context($scope.context.name, function(context){
              context.receivers = [added_receiver.id];
              $scope.admin.node.old_password = 'globaleaks';
              $scope.update($scope.admin.node);
              $scope.update(context);
              $location.path('/admin/receivers');
            });
          });
        });
      });
    };

  }
]);
