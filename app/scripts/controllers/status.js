GLClient.controller('StatusCtrl', function($scope, 
      $routeParams, $http) {
  var receipt_id = $routeParams.receipt_id;
  $http({method: 'GET', url: '/tip/'+receipt_id}).
    done(function(result) {
      // XXX add sanitization and validation
      var p_result = JSON.parse(result);
      $scope.tip = p_result['tip'];
      $scope.tip_data = p_result['tip_data'];
      $scope.folder = p_result['folder'];
      $scope.comment = p_result['comment'];
      $scope.receiver_selected = p_result['receiver_selected'];
  });
});
