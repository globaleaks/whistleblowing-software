GLClient.controller('StatusCtrl',
  ['$scope', '$routeParams', 'Tip', 'TipReceivers',
    'TipComments', 'localization',
  function($scope, $routeParams, Tip, TipReceivers, TipComments, localization) {

    var tip_id = {tip_id: $routeParams.tip_id};

    $scope.tip = Tip.get(tip_id, function(data){
      TipReceivers(tip_id, function(receivers){
       $scope.tip.receivers = receivers;
       console.log($scope.tip.receivers);
      });

      $scope.tip.comments = TipComments.query(tip_id);

    });
}]);
