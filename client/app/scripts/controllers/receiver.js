GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);

GLClient.controller('ReceiverFirstLoginCtrl', ['$scope', '$rootScope', '$location', 'changePasswordWatcher',
  function($scope, $rootScope, $location, changePasswordWatcher) {

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function () {
      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;
      $scope.preferences.pgp_key_public = '';

      $scope.preferences.$update(function () {
        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }

        $rootScope.successes.push({message: 'Updated your password!'});

        $location.path("/receiver/tips");

      });
    };

}]);

GLClient.controller('ReceiverPreferencesCtrl', ['$scope', '$rootScope', 'changePasswordWatcher', 'CONSTANTS',
  function($scope, $rootScope, changePasswordWatcher, CONSTANTS) {

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

    $scope.timezones = CONSTANTS.timezones;
    $scope.email_regexp = CONSTANTS.email_regexp;

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function () {
      if ($scope.preferences.pgp_key_remove === undefined) {
        $scope.preferences.pgp_key_remove = false;
      }
      if ($scope.preferences.pgp_key_public === undefined) {
        $scope.preferences.pgp_key_public = '';
      }

      $scope.preferences.$update(function () {

        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your password!'});
      });
    };

    $scope.pref_save = function() {
      $scope.preferences.password = '';
      $scope.preferences.old_password = '';

      if ($scope.preferences.pgp_key_remove === true) {
        $scope.preferences.pgp_key_public = '';
      }

      if ($scope.preferences.pgp_key_public !== undefined &&
          $scope.preferences.pgp_key_public !== '') {
        $scope.preferences.pgp_key_remove = false;
      }

      $scope.preferences.$update(function() {
        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }
        $rootScope.successes.push({message: 'Updated your preferences!'});
      });
    };

}]);

GLClient.controller('ReceiverLogsCtrl', ['$scope', '$http', '$route', '$location', 'ReceiverLogs',
  function($scope, $http, $location, $modal, ReceiverLogs) {

    $scope.warning = ReceiverLogs.query({filter: 'warning'});
    $scope.activities = ReceiverLogs.query({filter: 'activities'});
    console.log($scope.activities);

  }]);

GLClient.controller('ReceiverTipsCtrl', ['$scope',  '$http', '$route', '$location', '$modal', 'ReceiverTips',
  function($scope, $http, $route, $location, $modal, ReceiverTips) {
  $scope.tips = ReceiverTips.query();

  $scope.selected_tips = [];

  $scope.select_all = function () {
    $scope.selected_tips = [];
    angular.forEach($scope.tips, function (tip) {
      $scope.selected_tips.push(tip.id);
    });
  };

  $scope.deselect_all = function () {
    $scope.selected_tips = [];
  };

  $scope.tip_switch = function (e, id) {
    var index = $scope.selected_tips.indexOf(id);
    if (index > -1) {
      $scope.selected_tips.splice(index, 1);
    } else {
      $scope.selected_tips.push(id);
    }

    e.stopPropagation();
  };

  $scope.isSelected = function (id) {
    return $scope.selected_tips.indexOf(id) !== -1;
  }

  $scope.tip_delete_all = function () {
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_operation_delete_selected.html',
      controller: TipBulkOperationsCtrl,
      resolve: {
        selected_tips: function () {
          return $scope.selected_tips;
        },
        operation: function() {
          return 'delete';
        }
      }
    });
  };

  $scope.tip_postpone_all = function () {
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_operation_postpone_selected.html',
      controller: TipBulkOperationsCtrl,
      resolve: {
        selected_tips: function () {
          return $scope.selected_tips;
        },
        operation: function() {
          return 'postpone';
        }
      }
    });

  };

}]);

TipBulkOperationsCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'Tip', 'selected_tips', 'operation',
                        function ($scope, $http, $route, $location, $modalInstance, Tip, selected_tips, operation) {
  $scope.selected_tips = selected_tips;
  $scope.operation = operation;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
     $modalInstance.close();

    if (['postpone', 'delete'].indexOf(operation) === -1) {
      return;
    }

    return $http({method: 'PUT', url: '/rtip/operations', data:{
      'operation': $scope.operation,
      'rtips': $scope.selected_tips
    }}).success(function(data, status, headers, config){
      $scope.selected_tips = [];
      $route.reload();
    });

  };

}];
