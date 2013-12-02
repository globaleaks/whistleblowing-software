GLClient.controller('TipCtrl', ['$scope', '$http', '$route', '$location', '$modal', 'Tip', 'ReceiverTips',
  function($scope, $http, $route, $location, $modal, Tip, ReceiverTips) {

  $scope.tip_delete = function (id, global_delete) {
    $scope.tip_id = id;
    $scope.global_delete = global_delete;
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_delete.html',
      controller: ModalDeleteTipCtrl,
      resolve: {
        tip_id: function () {
          return $scope.tip_id;
        },
        global_delete: function () {
          return $scope.global_delete;
        }
      }
    });
  };

  $scope.tip_extend = function (id) {
    $scope.tip_id = id;

    var TipID = {tip_id: $scope.tip_id};
    new Tip(TipID, function(tip){
      var modalInstance = $modal.open({
        templateUrl: 'views/partials/tip_extend.html',
        controller: ModalPostponeTipCtrl,
        resolve: {
          tip: function () {
          return tip;
          }
        }
      });
    });
  };


}]);

ModalDeleteTipCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'tip_id', 'global_delete',
                     function ($scope, $http, $route, $location, $modalInstance, tip_id, global_delete) {

  $scope.tip_id = tip_id 
  $scope.global_delete = global_delete;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
      $modalInstance.close();
      return $http({method: 'DELETE', url: '/tip/' + tip_id, data:{global_delete: global_delete, is_pertinent: true}}).
                 success(function(data, status, headers, config){ $location.url('/receiver/tips'); });
  };
}];

ModalPostponeTipCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'tip',
                        function ($scope, $http, $route, $location, $modalInstance, tip) {

  $scope.tip = tip

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
     $modalInstance.close();
     $scope.tip.extend = true;

     // XXX this should be returned by the backend, but is not.
     $scope.tip.is_pertinent = false;

     $scope.tip.$update();
     $route.reload();
  };
}];

