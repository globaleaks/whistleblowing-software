GLClient.controller('WizardCtrl', ['$scope', '$location', '$route', '$http', '$uibModal', 'Authentication', 'Admin', 'AdminUtils', 'CONSTANTS',
                    function($scope, $location, $route, $http, $uibModal, Authentication, Admin, AdminUtils, CONSTANTS) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var finished = false;

    $scope.open_modal_allow_unencrypted = function() {
      if (!$scope.wizard.node.allow_unencrypted) {
        return;
      }

      var modalInstance = $uibModal.open({
        templateUrl: 'views/partials/disable_encryption.html',
        controller: 'DisableEncryptionCtrl'
      });

      modalInstance.result.then(function(result){
        $scope.wizard.node.allow_unencrypted = result;
      });
    };


    $scope.finish = function() {
      if (!finished) {
        $http.post('wizard', $scope.wizard).success(function() {
          alert($scope.wizard.admin.password);
          Authentication.login('admin', $scope.wizard.admin.password, function() {
            $scope.reload("/admin/landing");
          });
        });
      }
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

      var context = AdminUtils.new_context();

      $scope.wizard = {
        'node': {},
        'admin': {
          'mail_address': '',
          'password': ''
        },
        'receiver': receiver,
        'context': context
      };
    }
  }
]);
