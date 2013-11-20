/*global window */

GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);

GLClient.controller('ReceiverTipsCtrl', ['$scope', '$http', '$route', '$modal', 'ReceiverTips',
  function($scope, $http, $route, $modal, ReceiverTips) {
  $scope.tips = ReceiverTips.query();

  $scope.tip_delete = function (id) {
    $scope.tip_id = id;
    var modalInstance = $modal.open({
      templateUrl: '/views/receiver/tip_delete_modal.html',
      controller: ModalDeleteTipCtrl,
      resolve: {
        tip_id: function () {
          return $scope.tip_id;
        }
      }
    });

    modalInstance.tip_delete_confirm = function (id) {
      return $http.delete('/tip/' + id).success(function(data, status, headers, config){ $route.reload(); });
    };

  };

}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'ReceiverPreferences', 'changePasswordWatcher',
  function($scope, $rootScope, ReceiverPreferences, changePasswordWatcher) {

    $scope.tabs = [
      { title:"Password Configuration", template:"/views/receiver/preferences/tab1.html",
        ctrl: function($scope){
          $scope.id = 1;
        }    
      },
      { title:"Notification Settings", template:"/views/receiver/preferences/tab2.html",
        ctrl: function($scope){
          $scope.id = 2;
        }
      },
      { title:"Encryption Settings", template:"/views/receiver/preferences/tab3.html",
        ctrl: function($scope){
          $scope.id = 3;
        }
      }
    ];

    $scope.navType = 'pills';

    $scope.preferences = ReceiverPreferences.get();

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function() {

      /* default until PGP UI don't come back */
      $scope.preferences.gpg_key_armor = '';
      $scope.preferences.gpg_key_armor = '';

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

var ModalDeleteTipCtrl = function ($scope, $modalInstance, tip_id) {

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
    $modalInstance.tip_delete_confirm(tip_id);
    $modalInstance.close();
  };
};
