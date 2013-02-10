GLClient.controller('AdminReceiversCtrl', ['$scope', 'AdminReceivers',
function($scope, AdminReceivers) {

  $scope.new_receiver = $scope.admin.create_receiver;

  $scope.delete = function(receiver) {
    var idx = _.indexOf($scope.admin.receivers, receiver);

    receiver.$delete();
    $scope.admin.receivers.splice(idx, 1);
  };

  $scope.$watch('form')


}]);
