GLClient.controller('AdminAdvancedCtrl',
    ['$scope', 'AdminNotification',
  function($scope, AdminNotification) {
    $scope.delivery_method = '';
    $scope.adminNotification = AdminNotification.get();
    $scope.adminDelivery = {};

    $scope.saveNotificationSettings = function(notificationForm) {
      $scope.adminNotification.$save();
      notificationForm.$dirty = false;
      notificationForm.$pristine = true;
    };

}]);


