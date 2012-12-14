GLClient.controller('AdminReceiversCtrl', ['$scope', 'localization',
                    'AdminReceivers',
function($scope, localization, AdminReceivers) {

  $scope.adminReceivers = AdminReceivers.query();
  $scope.new_receiver = function() {
    var receiver = new AdminReceivers;
    receiver.notification_address = $scope.new_receiver_address;
    receiver.name = $scope.new_receiver_name;

    receiver.$save(function(created_receiver){
      $scope.adminReceivers.push(created_receiver);
    });
  }

}]);
