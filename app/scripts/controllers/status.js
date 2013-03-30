GLClient.controller('StatusCtrl',
  ['$scope', '$routeParams', 'Tip', '$cookies',
  function($scope, $routeParams, Tip, $cookies) {
    $scope.tip_id = $routeParams.tip_id;
    var TipID = {tip_id: $scope.tip_id};

    new Tip(TipID, function(tip){
      $scope.tip = tip;
    });

    $scope.newComment = function() {
      $scope.tip.comments.newComment($scope.newCommentContent);
      $scope.newCommentContent = '';
    };

    if ($cookies['role'] === 'wb') {
      $scope.whistleblower_tip_id = $cookies['tip_id'];
      $scope.uploadedFiles = [];
      $scope.uploadingFiles = [];
    };

}]);
