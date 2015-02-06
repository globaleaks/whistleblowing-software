GLClient.controller('EmbeddedReceiptCtrl',
  ['$scope', '$rootScope', '$location', 'WhistleblowerTip',
  function($scope, $rootScope, $location, WhistleblowerTip) {

  $rootScope.embedded = true;

  $scope.$watch("language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.language;
    }
  });

  $scope.view_tip = function(keycode) {
    keycode = keycode.replace(/\D/g,'');
    WhistleblowerTip(keycode, function() {
      $location.path('/status');
    });
  };

}]).
controller('EmbeddedSubmissionCtrl',
  ['$scope', '$rootScope', '$location', 'WhistleblowerTip',
  function($scope, $rootScope, $location, WhistleblowerTip) {

  $rootScope.embedded = true;

}]);

