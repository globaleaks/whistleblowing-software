GLClient.controller('AdminReceiversCtrl', ['$scope',
function($scope) {

  $scope.new_receiver = $scope.admin.create_receiver;

  $scope.delete = function(receiver) {
    var idx = _.indexOf($scope.admin.receivers, receiver);

    receiver.$delete(function(){
      $scope.admin.receivers.splice(idx, 1);
    });

  };

}]);
