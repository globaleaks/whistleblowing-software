GL.
controller("AdminMailCtrl", ["$scope", "AdminNotificationResource",
  function($scope, AdminNotificationResource) {

  $scope.tabs = [
    {
      title:"Settings",
      template:"views/admin/notifications/tab1.html"
    },
    {
      title:"Templates",
      template:"views/admin/notifications/tab2.html"
    }
  ];

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.resources.notification)
    .$promise.then(function() { return $scope.Utils.runAdminOperation("test_mail"); }, function() { });
  };
}]);
