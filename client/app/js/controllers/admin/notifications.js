GLClient.
controller("AdminMailCtrl", ["$scope", "$http", "AdminNotificationResource",
  function($scope, $http, AdminNotificationResource) {

  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/notifications/tab1.html"
    },
    {
      title:"Notification templates",
      template:"views/admin/notifications/tab2.html"
    }
  ];

  var sendTestMail = function() {
    var req = {
      "operation": "test_mail",
      "args": {}
    };

    return $http({method: "PUT", url: "admin/config", data: req});
  };

  $scope.resetSMTPConfiguration = function() {
    $scope.resources.notification.smtp_server = "mail.globaleaks.org";
    $scope.resources.notification.smtp_port = 9267;
    $scope.resources.notification.smtp_username = "globaleaks";
    $scope.resources.notification.smtp_password = "globaleaks";
    $scope.resources.notification.smtp_source_email = "notification@mail.globaleaks.org";
    $scope.resources.notification.smtp_security = "TLS";
    $scope.resources.notification.smtp_authentication = true;

    $scope.Utils.update($scope.resources.notification);
  };

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.resources.notification)
    .$promise.then(function() { return sendTestMail(); }, function() { });
  };
}]);
