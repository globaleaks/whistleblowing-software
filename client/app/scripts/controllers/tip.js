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

        fn($scope.tip);
      });
    }
  }, true);

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

     if (operation == 'postpone') {
       $scope.tip.operation = operation;
       $scope.tip.$update(function() {
         $route.reload();
       });
     } else if (operation == 'delete') {
       return $http({method: 'DELETE', url: '/rtip/' + tip_id, data:{}}).
             success(function(data, status, headers, config){ 
               $location.url('/receiver/tips');
               $route.reload();
             });
     }

  };

}];

