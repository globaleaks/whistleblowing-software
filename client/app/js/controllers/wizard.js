GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', '$uibModal', 'locationForce', 'Authentication', 'Admin', 'AdminUtils', 'CONSTANTS', 'glbcUserKeyGen',
                    function($scope, $rootScope, $location, $route, $http, $uibModal, locationForce, Authentication, Admin, AdminUtils, CONSTANTS, glbcUserKeyGen) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var default_user_pass = "globaleaks";

    $scope.nextStep = function() {
      if ($scope.step === 2) {
        $rootScope.blockUserInput = true;
        $scope.keyGenFin = false;
        glbcUserKeyGen.setup();
        glbcUserKeyGen.startKeyGen();
        $http.post('wizard', $scope.wizard).then(function() {
          return Authentication.login('admin', default_user_pass);
        }).then(function() {
          glbcUserKeyGen.addPassphrase(default_user_pass, $scope.admin_password);
          return glbcUserKeyGen.vars.promises.ready;
        })
        .then(function() {
          $scope.keyGenFin = true;
          $rootScope.blockUserInput = false;
        });
      }

      $scope.step += 1;
    }

    $scope.finish = function() {
      $location.path(Authentication.session.auth_landing_page);
      $scope.reload("/admin/landing");
      locationForce.clear();
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

      $scope.admin_password = "";
      $scope.wizard = {
        'node': {},
        'admin': {
          'mail_address': '',
        },
        'receiver': receiver,
        'context': context
      };
    }
}]);
