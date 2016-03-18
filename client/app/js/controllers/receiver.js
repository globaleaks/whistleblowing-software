GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]);


GLClient.controller('ReceiverTipsCtrl', ['$scope',  '$http', '$route', '$location', '$uibModal', 'ReceiverTips',
  function($scope, $http, $route, $location, $uibModal, ReceiverTips) {
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

  $scope.tip_export_all = function () {
    export_tips($scope.selected_tips, $scope.session, $http);
    var modalInstance = $uibModal.open({
      templateUrl: 'views/partials/tip_operation_export_selected.html',
      controller: TipBulkOperationsCtrl,
      resolve: {
        selected_tips: function () {
          return $scope.selected_tips;
        },
        operation: function() {
          return 'export';
        }
      }
    });
  };

  $scope.tip_delete_all = function () {
    var modalInstance = $uibModal.open({
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
    var modalInstance = $uibModal.open({
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

TipBulkOperationsCtrl = ['$scope', '$http', '$route', '$location', '$q', '$uibModalInstance', 'selected_tips', 'operation',
                        function ($scope, $http, $route, $location, $q, $uibModalInstance, selected_tips, operation) {
  $scope.selected_tips = selected_tips;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
     $uibModalInstance.close();

    switch (operation) {
      case 'export':
          export_tips(selected_tips, $scope.session, $http);
          return;
      case 'postpone':
      case 'delete':
          return $http({method: 'PUT', url: '/rtip/operations', data:{
            'operation': $scope.operation,
            'rtips': $scope.selected_tips
          }}).success(function(data, status, headers, config){
            $scope.selected_tips = [];
            $route.reload();
          });
      default:
          return;
    }
  };
}];

function export_tips(selected_tips, session, $http) {
  angular.forEach(selected_tips, function(tip) {
             // Chain the series of http post's together
             $http({method: 'POST', url: '/rtip/'+tip+'/export', 
                data: session.id})
  })
}
