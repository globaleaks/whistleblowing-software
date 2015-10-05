GLClient.controller('CustodianIdentityAccessRequestsCtrl', ['$scope',  '$http', '$route', '$location', '$modal', 'IdentityAccessRequests',
  function($scope, $http, $route, $location, $modal, IdentityAccessRequests) {
  $scope.iars = IdentityAccessRequests.query();
}]);
