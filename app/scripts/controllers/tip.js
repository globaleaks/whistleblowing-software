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

    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_extend.html',
      controller: ModalPostponeTipCtrl,
      resolve: {
        tip_id: function () {
          return $scope.tip_id;
        }
      }
    });

  };

  $scope.$watch('msg_receiver_selected', function(){
    if ($scope.msg_receiver_selected) {
      messageResource.query({receiver_id: $scope.msg_receiver_selected}, function(messageCollection){
        $scope.tip.messages = messageCollection;

        $scope.tip.messages.newMessage = function(content) {
          var m = new messageResource({receiver_id: $scope.msg_receiver_selected});
          m.content = content;
          m.$save(function(newMessage) {
            $scope.tip.messages.unshift(newMessage);
          });
        };

        // XXX perhaps make this return a lazyly instanced item.
        // look at $resource code for inspiration.
        fn($scope.tip);
      });
    }
  }, true);

}]);

ModalDeleteTipCtrl = ['$scope', '$http', '$route', '$location', '$modalInstance', 'tip_id', 'global_delete',
                     function ($scope, $http, $route, $location, $modalInstance, tip_id, global_delete) {

  $scope.tip_id = tip_id;
  $scope.global_delete = global_delete;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
      $modalInstance.close();
      return $http({method: 'DELETE', url: '/rtip/' + tip_id, data:{global_delete: global_delete, is_pertinent: true}}).
                 success(function(data, status, headers, config){ 
                                                                  $location.url('/receiver/tips');
                                                                  $route.reload();
                                                                });
  };
}];

ModalPostponeTipCtrl = ['$scope', '$http', '$route', '$location', 'Tip', '$modalInstance', 'tip_id',
                        function ($scope, $http, $route, $location, Tip, $modalInstance, tip_id) {

  $scope.tip_id = tip_id;

  var TipID = {tip_id: $scope.tip_id};
  new Tip(TipID, function(tip){
    $scope.tip = tip;
  });

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

