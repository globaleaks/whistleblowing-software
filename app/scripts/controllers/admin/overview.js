GLClient.controller('OverviewCtrl', ['$scope',
  function($scope) {
      $scope.overview_users = ReceiverOverview.query();
      $scope.overview_tips = TipOverview.query();
}]);

