GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'WhistleblowerTip',
  function($scope, $rootScope, WhistleblowerTip) {

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

}]);
