GLClient.
controller("MainCtrl", ["$rootScope", function($rootScope) {
  if (!$rootScope.page) {
    $rootScope.setPage($rootScope.public.node.landing_page);
  }
}]);
