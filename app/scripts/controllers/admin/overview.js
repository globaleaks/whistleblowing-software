GLClient.controller('OverviewCtrl', ['$scope', 'ReceiverOverview', 'TipOverview',
  function($scope, ReceiverOverview, TipOverview) {
      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
}]);
