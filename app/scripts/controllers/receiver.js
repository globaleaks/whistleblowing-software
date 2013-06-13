/*global window */

GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);

GLClient.controller('ReceiverTipsCtrl', ['$scope', 'ReceiverTips',
  function($scope, ReceiverTips) {
  $scope.tips = ReceiverTips.query();
}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'ReceiverPreferences', 'changePasswordWatcher',
  function($scope, $rootScope, ReceiverPreferences, changePasswordWatcher) {
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

      $scope.preferences.file_notification = $scope.copy_file_notification;
      $scope.preferences.comment_notification = $scope.copy_comment_notification;
      $scope.preferences.tip_notification = $scope.copy_tip_notification;
      $scope.preferences.gpg_key_remove = $scope.copy_gpg_key_remove;


      $scope.preferences.password = '';
      $scope.preferences.old_password = '';

      if ($scope.preferences.gpg_key_armor != undefined &&
          $scope.preferences.gpg_key_armor != '') {
        $scope.preferences.gpg_key_remove = false;
      }
      if ($scope.preferences.gpg_key_remove == true) {
        $scope.preferences.gpg_key_armor = '';
      }

      $scope.preferences.$update(function(){

        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    }

}]);





