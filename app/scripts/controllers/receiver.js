/* global window */

GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'ReceiverPreferences', 'changePasswordWatcher',
  function($scope, $rootScope, ReceiverPreferences, changePasswordWatcher) {

    $scope.tabs = [
      {
        title: "Password Configuration",
        template: "views/receiver/preferences/tab1.html",
        ctrl: TabCtrl
      },
      {
        title: "Notification Settings",
        template: "views/receiver/preferences/tab2.html",
        ctrl: TabCtrl
      },
      {
        title:"Encryption Settings",
        template:"views/receiver/preferences/tab3.html",
        ctrl: TabCtrl
      }
    ];

    $scope.navType = 'pills';

    $scope.preferences = ReceiverPreferences.get();

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function() {

      if ($scope.preferences.gpg_key_remove == undefined) {
        $scope.preferences.gpg_key_remove = false;
      }
      if ($scope.preferences.gpg_key_armor == undefined) {
        $scope.preferences.gpg_key_armor = '';
      }

      $scope.preferences.$update(function(){

        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your password!'});
      });
    }

    $scope.pref_save = function() {

      $scope.preferences.password = '';
      $scope.preferences.old_password = '';

      if ($scope.preferences.gpg_key_remove == true) {
        $scope.preferences.gpg_key_armor = '';
      }

      if ($scope.preferences.gpg_key_armor !== undefined &&
          $scope.preferences.gpg_key_armor != '') {
        $scope.preferences.gpg_key_remove = false;
      }

      $scope.preferences.$update(function(){

        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    }

}]);

GLClient.controller('ReceiverTipsCtrl', ['$scope', '$http', '$route', '$location', '$modal', 'ReceiverTips',
  function($scope, $http, $route, $location, $modal, ReceiverTips) {
  $scope.tips = ReceiverTips.query();
}]);
