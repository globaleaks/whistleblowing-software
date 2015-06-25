GLClient.controller('TipCtrl', ['$rootScope', '$scope', '$http', '$route', '$location', '$modal',
  function($rootScope, $scope, $http, $route, $location, $modal) {

  $scope.tip_delete = function () {
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_operation_delete.html',
      controller: TipOperationsCtrl,
      resolve: {
        tip: function () {
          return $scope.tip;
        },
        operation: function () {
          return 'delete';
        }
      }
    });
  };

  $scope.tip_postpone = function () {
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_operation_postpone.html',
      controller: TipOperationsCtrl,
      resolve: {
        tip: function () {
          return $scope.tip;
        },
        operation: function () {
          return 'postpone';
        }
      }
    });
  };

}]);

TipOperationsCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'Tip', 'tip', 'operation',
                        function ($scope, $http, $route, $location, $modalInstance, Tip, tip, operation) {
  $scope.tip = tip;
  $scope.operation = operation;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
     $modalInstance.close();

     if ($scope.operation === 'postpone') {
       $scope.tip.operation = $scope.operation;
       $scope.tip.$update(function() {
         $route.reload();
       });
     } else if ($scope.operation === 'delete') {
       return $http({method: 'DELETE', url: '/rtip/' + tip.id, data:{}}).
             success(function(data, status, headers, config){
               $location.url('/receiver/tips');
               $route.reload();
             });
     }
  };
}];
