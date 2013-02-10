GLClient.controller('AdminReceiversCtrl', ['$scope', 'AdminReceivers',
function($scope, AdminReceivers) {

  $scope.new_receiver = function() {
    var receiver = new AdminReceivers;

    receiver.name = $scope.new_receiver_name;
    receiver.description = $scope.new_receiver_name;

    receiver.notification_selected = 'email';
    receiver.notification_fields = '';

    receiver.languages = ['en', 'it'];

    // Under here go default settings
    receiver.can_postpone_expiration = true;
    receiver.can_configure_notification = true;
    receiver.can_configure_delivery = true;
    receiver.can_delete_submission = true;

    receiver.delivery_selected = 'local';
    receiver.delivery_fields = '';

    receiver.receiver_level = 1;

    receiver.tags = [];
    receiver.contexts =  [];

    receiver.$save(function(created_receiver){
      $scope.adminReceivers.push(created_receiver);
    });
  };

  $scope.delete_receiver = function(receiver) {
    var idx = _.indexOf($scope.adminReceivers, receiver);
    window.antanisblinda = $scope.adminReceivers;

    receiver.$delete();
    $scope.adminReceivers.splice(idx, 1);
  };


}]);
