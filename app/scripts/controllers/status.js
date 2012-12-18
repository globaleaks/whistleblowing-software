GLClient.controller('StatusCtrl',
  ['$scope', '$routeParams', 'Tip', 'TipReceivers',
    'TipComments', 'localization',
  function($scope, $routeParams, Tip, TipReceivers, TipComments, localization) {

    var tip_id = {tip_id: $routeParams.tip_id};

    $scope.tip = Tip.get(tip_id, function(data){
      console.log("Got this data from server");
      console.log(data);

      $scope.tip.receivers = TipReceivers.get(tip_id);

      // , function(receivers){
      //   angular.forEach(receivers, function(receiver){
      //     $scope.receiver_list.push(receiver);
      //   });
      // });

      $scope.tip.comments = TipComments.get(tip_id);

      $scope.tip.receivers.get();

    });


}]);
