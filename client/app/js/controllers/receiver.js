GLClient.controller('ReceiverTipsCtrl', ['$scope',  '$filter', '$http', '$route', '$location', '$uibModal', 'RTipExport', 'ReceiverTips',
  function($scope, $filter, $http, $route, $location, $uibModal, RTipExport, ReceiverTips) {
  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;

  $scope.tips = ReceiverTips.query(function(tips) {
    angular.forEach(tips, function (tip) {
      tip.context = $scope.contexts_by_id[tip.context_id];
      tip.context_name = tip.context.name;
    });
  });

  $scope.filteredTips = $scope.tips;

  $scope.$watch('search', function (value) {
    if (value != undefined) {
      $scope.currentPage = 1;
      $scope.filteredTips = $filter('filter')($scope.tips, value);
    }
  });

  $scope.exportTip = RTipExport;

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

  $scope.tip_switch = function (id) {
    var index = $scope.selected_tips.indexOf(id);
    if (index > -1) {
      $scope.selected_tips.splice(index, 1);
    } else {
      $scope.selected_tips.push(id);
    }
  };

  $scope.isSelected = function (id) {
    return $scope.selected_tips.indexOf(id) !== -1;
  };

  $scope.tip_delete_all = function () {
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_delete_selected.html',
      controller: 'TipBulkOperationsCtrl',
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
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_postpone_selected.html',
      controller: 'TipBulkOperationsCtrl',
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
}]).
controller('TipBulkOperationsCtrl', ['$scope', '$http', '$route', '$location', '$uibModalInstance', 'selected_tips', 'operation',
  function ($scope, $http, $route, $location, $uibModalInstance, selected_tips, operation) {
  $scope.selected_tips = selected_tips;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
     $uibModalInstance.close();

    if (['postpone', 'delete'].indexOf(operation) === -1) {
      return;
    }

    return $http({method: 'PUT', url: 'rtip/operations', data:{
      'operation': $scope.operation,
      'rtips': $scope.selected_tips
    }}).then(function(){
      $scope.selected_tips = [];
      $route.reload();
    });
  };
}]);
