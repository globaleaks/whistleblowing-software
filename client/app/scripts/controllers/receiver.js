GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
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
