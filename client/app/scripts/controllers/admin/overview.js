GLClient.controller('OverviewCtrl', ['$scope', '$location', 'ReceiverOverview', 'TipOverview', 'FileOverview',
  function($scope, $location, ReceiverOverview, TipOverview, FileOverview) {

      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();

      var current_menu = $location.path().split('/').slice(-1);
      current_menu += "_overview";
      $scope.active = {};
      $scope.active[current_menu] = "active";
}]);
