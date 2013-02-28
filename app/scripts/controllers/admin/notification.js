GLClient.controller('AdminNotificationCtrl', ['$scope',
function($scope) {

   $scope.updateNotification = function(notification) {
       $scope.update(notification);
   }

}]);
