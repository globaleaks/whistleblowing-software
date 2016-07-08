GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', 'locationForce', 'Authentication', 'Admin', 'AdminUtils', 'CONSTANTS', 'glbcUtil', 'glbcUserKeyGen',
                    function($scope, $rootScope, $location, $route, $http, locationForce, Authentication, Admin, AdminUtils, CONSTANTS, glbcUtil, glbcUserKeyGen) {
    $scope.nextStep = function() {
      if ($scope.step === 2) {
        $rootScope.blockUserInput = true;
        glbcUserKeyGen.startKeyGen();
        glbcUserKeyGen.addPassphrase($scope.admin_password, $scope.admin_password);
        glbcUserKeyGen.vars.promises.ready.then(function(body) {
          $scope.wizard.admin.auth = body;
          return $http.post('wizard', $scope.wizard).then(function() {
            $scope.wizardComplete = true;
            $rootScope.blockUserInput = false;
          });
        });
      }

      $scope.step += 1;
    }

    $scope.firstAdminLogin = function() {
      console.log($scope.admin_password);
      return Authentication.login('admin', $scope.admin_password).then(function() {
        $location.path(Authentication.session.auth_landing_page);
        $scope.reload("/admin/landing");
        locationForce.clear();
      });
    };

    if ($scope.node.wizard_done) {
      /* if the wizard has been already performed redirect to the homepage */
      $location.path('/');
    }

    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;
    $scope.admin_salt = glbcUtil.generateRandomSalt();
    $scope.admin_password = "";
    $scope.wizardComplete = false;
    glbcUserKeyGen.setup($scope.admin_salt);

    var receiver = AdminUtils.new_user();
    receiver.username = 'receiver';
    receiver.password = ''; // this causes the system to set the default password
                            // the system will then force the user to change the password
                            // at first login

    var context = AdminUtils.new_context();

    $scope.admin

    $scope.wizard = {
      'node': {},
      'admin': {
        'salt': $scope.admin_salt,
        'auth': {},
        'mail_address': '',
      },
      'receiver': receiver,
      'context': context
    };
}]);
