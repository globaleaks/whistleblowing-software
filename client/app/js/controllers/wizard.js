GLClient.controller('WizardCtrl', ['$scope', '$location', '$route', '$http', '$uibModal', 'Authentication', 'Admin', 'DefaultAppdata', 'glbcUser', 'CONSTANTS', function($scope, $location, $route, $http, $uibModal, Authentication, Admin, DefaultAppdata, glbcUser, CONSTANTS) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var finished = false;

    $scope.open_modal_allow_unencrypted = function() {
      if (!$scope.admin.node.allow_unencrypted) {
        return;
      }

      var modalInstance = $uibModal.open({
        templateUrl: 'views/partials/disable_encryption.html',
        controller: 'DisableEncryptionCtrl'
      });

      modalInstance.result.then(function(result){
        $scope.admin.node.allow_unencrypted = result;
      });
    };


    $scope.finish = function() {
      if (!finished) {

        var admin = {
          'mail_address': $scope.admin_mail_address,
        };

        $scope.wizard = {
          'node': $scope.admin.node,
          'admin': admin,
          'receiver': $scope.receiver,
          'context': $scope.context
        };

        $http.post('admin/wizard', $scope.wizard).then(function() {
          return glbcUser.changePassword('admin', $scope.password, 'globaleaks');
        }).then(function() {
          $scope.reload("/admin/landing");
        });
      }
    };
    
    if ($scope.node.wizard_done) {
      /* if the wizard has been already performed redirect to the homepage */
      $location.path('/');
    } else {
      Authentication.login('admin', 'globaleaks', function(){
        $scope.admin = new Admin(function() {
          $scope.receiver = new $scope.admin.new_user();
          $scope.receiver.username = 'receiver';
          $scope.receiver.password = ''; // this causes the system to set the default password
                                         // the system will then force the user to change the password
                                         // at first login
          $scope.context = $scope.admin.new_context();
        });
      });
    }
}]);
