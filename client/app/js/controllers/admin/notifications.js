GL.
controller("AdminMailCtrl", ["$scope", "AdminNotificationResource",
  function($scope, AdminNotificationResource) {

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

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.resources.notification)
    .$promise.then(function() { return $scope.Utils.applyConfig("test_mail"); }, function() { });
  };
}]);
