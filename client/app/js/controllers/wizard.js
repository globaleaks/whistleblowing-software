GLClient.controller('WizardCtrl', ['$scope', '$rootScope', '$location', '$route', '$http', 'locationForce', 'Authentication', 'Admin', 'AdminUtils', 'CONSTANTS', 'glbcUtil', 'glbcUserKeyGen',
                    function($scope, $rootScope, $location, $route, $http, locationForce, Authentication, Admin, AdminUtils, CONSTANTS, glbcUtil, glbcUserKeyGen) {
    $scope.email_regexp = CONSTANTS.email_regexp;

    $scope.step = 1;

    var default_user_pass = "globaleaks";

    $scope.wizardComplete = false;

    $scope.nextStep = function() {
      if ($scope.step === 2) {
        $rootScope.blockUserInput = true;
        glbcUserKeyGen.setup($scope.wizard.admin.salt);
        glbcUserKeyGen.startKeyGen();
        glbcUserKeyGen.addPassphrase(default_user_pass, $scope.admin_password);
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
        'salt': glbcUtil.generateRandomSalt(),
        'auth': {},
        'mail_address': '',
      },
      'receiver': receiver,
      'context': context
    };
}]);
