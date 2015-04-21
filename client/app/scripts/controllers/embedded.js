GLClient.controller('EmbeddedReceiptCtrl',
  ['$scope', '$rootScope', '$location', 'WBReceipt',
  function($scope, $rootScope, $location, WBReceipt) {

  $rootScope.embedded = true;

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

}]).
controller('EmbeddedSubmissionCtrl',
  ['$scope', '$rootScope', '$location',
  function($scope, $rootScope, $location) {

  $rootScope.embedded = true;

}]);

