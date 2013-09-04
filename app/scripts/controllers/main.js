GLClient.controller('MainCtrl', ['$scope', 'Templates',
    function($scope, Templates) {
  $scope.Templates = Templates;
  $scope.started = true;
}]);
