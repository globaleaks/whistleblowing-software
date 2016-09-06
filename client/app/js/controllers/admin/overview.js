GLClient.controller('OverviewCtrl', ['$scope', '$location', 'AdminUserResource', 'TipOverview', 'FileOverview',
  function($scope, $location, AdminUserResource, TipOverview, FileOverview) {
      $scope.users = AdminUserResource.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();

      var current_menu = $location.path().split('/').slice(-1);
      current_menu += "_overview";
      $scope.active = {};
      $scope.active[current_menu] = "active";
}]);
