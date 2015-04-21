GLClient.controller('UserCtrl',
  ['$scope', '$rootScope', '$location', 'WBReceipt',
  function($scope, $rootScope, $location, WBReceipt) {

  $scope.$watch("language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.language;
    }
  });

  $scope.view_tip = function(keycode) {
    keycode = keycode.replace(/\D/g,'');
    WBReceipt(keycode, function() {
      $location.path('/status');
    });
  };

}]);
