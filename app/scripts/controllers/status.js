GLClient.controller('StatusCtrl', ['$scope', '$routeParams',
    'Tip', 'localization', function($scope, $routeParams, Tip,
      localization) { $scope.receipt_id =
        $routeParams.receipt_id;
  $scope.tip = new Tip();
  $scope.tip.tip_id = $scope.receipt_id;
  $scope.tip.$get(function(){
    $scope.receiver_list = [];
    angular.forEach($scope.tip.receiver_map, function(value){
      var receiver = {};
      receiver = value;
      receiver.name = value.receiver_gus;
      $scope.receiver_list.append(receiver.receiver_gus);
    });
  });
  $scope.node_info = localization.node_info;

}]);
