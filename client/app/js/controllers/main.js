GLClient.
controller("MainCtrl", ["$rootScope", function($rootScope) {
  if (!$rootScope.page) {
    $rootScope.setPage($rootScope.node.landing_page);
  }
}]);
