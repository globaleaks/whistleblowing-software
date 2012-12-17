GLClient.controller('AdminReceiversCtrl', ['$scope', 'localization',
                    'AdminReceivers',
function($scope, localization, AdminReceivers) {

  $scope.adminReceivers = AdminReceivers.query();

  $scope.new_receiver = function() {
    var receiver = new AdminReceivers;

    receiver.notification_address = $scope.new_receiver_address;
    receiver.name = $scope.new_receiver_name;
    receiver.description = $scope.new_receiver_name;

    receiver.fields = $scope.new_receiver_fields;
    receiver.escalation_threshold =  42;
    receiver.file_max_download = 42;
    receiver.tip_max_access = 42;
    receiver.selectable_receiver = true;
    receiver.tip_timetolive = 42;

    receiver.$save(function(created_receiver){
      $scope.adminReceivers.push(created_receiver);
    });
  }

}]);
