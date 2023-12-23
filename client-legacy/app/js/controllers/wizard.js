GL.controller("WizardCtrl", ["$scope", "$location", "$http", "Authentication", "GLTranslate",
                    function($scope, $location, $http, Authentication, GLTranslate) {
  /* if the wizard has been already performed redirect to the homepage */
  if ($scope.public.node.wizard_done) {
    $location.path("/");
    return;
  }

  $scope.step = 1;

  var completed = false;

  $scope.complete = function() {
    if (completed) {
        return;
    }

    completed = true;

    $http.post("api/wizard", $scope.wizard).then(function() {
      $scope.step += 1;
    });
  };

  $scope.goToAdminInterface = function() {
    Authentication.login(0, $scope.wizard.admin_username, $scope.wizard.admin_password, "", "").then(function() {
      $scope.reload("/admin/home");
    });
  };

  $scope.config_profiles = [
    {
      name:  "default",
      title: "Default",
      active: true
    }
  ];

  $scope.selectProfile = function(name) {
    angular.forEach($scope.config_profiles, function(p) {
      p.active = p.name === name ? true : false;
      if (p.active) {
        $scope.wizard.profile = p.name;
      }
    });
  };

  $scope.wizard = {
    "node_language": GLTranslate.state.language,
    "node_name": "",
    "admin_username": "",
    "admin_name": "",
    "admin_mail_address": "",
    "admin_password": "",
    "admin_escrow": true,
    "receiver_username": "",
    "receiver_name": "",
    "receiver_mail_address": "",
    "receiver_password": "",
    "skip_admin_account_creation": false,
    "skip_recipient_account_creation": false,
    "profile": "default",
    "enable_developers_exception_notification": false
  };
}]);
