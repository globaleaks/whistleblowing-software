GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'WhistleblowerTip',
  function($scope, $rootScope, WhistleblowerTip) {

  $scope.$watch("language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.language;
    }
  });

  $scope.view_tip = function(receipt) {
    receipt = receipt.replace(/\D/g,'');
    WhistleblowerTip(receipt, function() {
      $location.path('/status');
    });
  };

}]);
