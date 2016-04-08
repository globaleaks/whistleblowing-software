GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]).
controller('ReceiverTipsCtrl', ['$scope',  '$http', '$route', '$location', '$uibModal', 'RTipExport', 'ReceiverTips',
  function($scope, $http, $route, $location, $uibModal, RTipExport, ReceiverTips) {
  $scope.tips = ReceiverTips.query();
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

  function selectTips() {
    var selected_tips = $scope.tips.filter(function(tip) {
      return $scope.selected_tips.indexOf(tip.id) > -1;
    });
    return selected_tips;
  }

  $scope.tip_export_all = function() {
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_export_selected.html',
      controller: 'TipBulkOperationsCtrl',
      resolve: {
        selected_tips: selectTips,
        operation: function() { return 'export'; },
      },
    });
  };

  $scope.tip_delete_all = function () {
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_delete_selected.html',
      controller: 'TipBulkOperationsCtrl',
      resolve: {
        selected_tips: selectTips,
        operation: function() { return 'delete'; },
      },
    });
  };

  $scope.tip_postpone_all = function () {
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_postpone_selected.html',
      controller: 'TipBulkOperationsCtrl',
      resolve: {
        selected_tips: selectTips,
        operation: function() { return 'postpone'; }, 
      },
    });
  };
}]).
controller('TipBulkOperationsCtrl', ['$scope', '$q', '$http', '$route', '$location', '$uibModalInstance', 'RTipExport', 'selected_tips', 'operation',
                        function ($scope, $q, $http, $route, $location, $uibModalInstance, RTipExport, selected_tips, operation) {
  $scope.selected_tips = selected_tips;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
   $uibModalInstance.close();

    switch (operation) {
      case 'postpone':
      case 'delete':
        tip_ids = $scope.selected_tips.map(function(tip){ return tip.id; });

        $http({method: 'PUT', url: '/rtip/operations', data:{
              'operation': $scope.operation,
              'rtips': tip_ids,
        }}).success(function(){
              $route.reload();
        });
        return;
      case 'export':
        export_promises = $scope.selected_tips.map(function(tip) {
          return RTipExport(tip);
        });

        $q.all(export_promises); 
        // Do not reload the page b/c further ops may be desired on selected_tips
        return;
      default:
        return;
    }
  };
}]);
