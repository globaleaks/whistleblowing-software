/*global window */

GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
  console.log(current_menu);

}]);

GLClient.controller('ReceiverTipsCtrl', ['$scope', 'ReceiverTips',
  function($scope, ReceiverTips) {
  $scope.tips = ReceiverTips.query();
}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'ReceiverPreferences', 'changePasswordWatcher',
  function($scope, $rootScope, ReceiverPreferences, changePasswordWatcher) {
    $scope.preferences = ReceiverPreferences.get();

    changePasswordWatcher($scope, "preferences.old_password", "preferences.password");

    $scope.save = function() {
      $scope.preferences.$update(function(){
        if (!$rootScope.successes) {
          $rootScope.successes = [];
        };
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    }

}]);





