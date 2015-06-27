GLClient.controller('TipCtrl', ['$scope', '$http', '$route', '$location', '$modal',
  function($scope, $http, $route, $location, $modal) {

  $scope.tip_delete = function (id) {
    $scope.tip_id = id;

    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_delete.html',
      controller: TipOperationsCtrl,
      resolve: {
        tip_id: function () {
          return $scope.tip_id;
        }
      }
    });
  };

  $scope.tip_postpone = function (id) {
    $scope.tip_id = id;

    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_postpone.html',
      controller: TipOperationsCtrl,
      resolve: {
        tip_id: function () {
          return $scope.tip_id;
        }
      }
    });

  };

}]);

TipOperationsCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'Tip', 'tip_id',
                        function ($scope, $http, $route, $location, $modalInstance, Tip, tip_id) {

  $scope.tip_id = tip_id;

  var TipID = {tip_id: $scope.tip_id};
  new Tip(TipID, function(tip){
    $scope.tip = tip;
  });

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function (operation) {
     $modalInstance.close();

     if (operation === 'postpone') {
       $scope.tip.operation = operation;
       $scope.tip.$update(function() {
         $route.reload();
       });
     } else if (operation === 'delete') {
       return $http({method: 'DELETE', url: '/rtip/' + tip_id, data:{}}).
             success(function(data, status, headers, config){ 
               $location.url('/receiver/tips');
               $route.reload();
             });
     }

  };

}];

