GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope',
  function($scope, $rootScope) {

  $scope.$watch("language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.language;
    }
  });

}]);