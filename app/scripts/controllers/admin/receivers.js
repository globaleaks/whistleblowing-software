GLClient.controller('AdminReceiversCtrl', ['$scope', 'AdminReceivers',
function($scope, AdminReceivers) {

  $scope.new_receiver = function() {
    var receiver = new AdminReceivers;

    receiver.name = $scope.new_receiver_name;

    receiver.description = '';
    receiver.password = null;

    receiver.notification_selected = 'email';
    receiver.notification_fields = {'mail_address': ''};

    receiver.languages = [];

    // Under here go default settings
    receiver.can_postpone_expiration = true;
    receiver.can_configure_notification = true;
    receiver.can_configure_delivery = true;
    receiver.can_delete_submission = true;

    receiver.receiver_level = 1;

    receiver.tags = [];
    receiver.contexts =  [];

    receiver.$save(function(created_receiver){
      $scope.adminReceivers.push(created_receiver);
    });
  };

  $scope.delete_receiver = function(receiver) {
    var idx = _.indexOf($scope.adminReceivers, receiver);

    receiver.$delete();
    $scope.adminReceivers.splice(idx, 1);
  };


}]);
