GLClient.controller('StatusCtrl',
  ['$scope', '$routeParams', 'Tip', 'localization',
  function($scope, $routeParams, Tip, localization) {
    $scope.tip_id = $routeParams.tip_id;
    var TipID = {tip_id: $scope.tip_id};

    Tip(TipID, function(tip){
      $scope.tip = tip;
    });

    $scope.newComment = function() {
      $scope.tip.comments.newComment($scope.newCommentContent);
    };

}]);
