GLClient.controller('OverviewCtrl', ['$scope',
  function($scope) {
  $scope.overview_users = UserOverview.query();
}]);

