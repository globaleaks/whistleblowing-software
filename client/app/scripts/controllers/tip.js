GLClient.controller('TipCtrl', ['$rootScope', '$scope', '$http', '$route', '$location', '$modal',
  function($rootScope, $scope, $http, $route, $location, $modal) {

  $scope.tipall = function () {

    $rootScope.selected_tip_list = [];
    $('.checkboxes').each(function (i, checkbox) {

      /* why otherwise say "undefined not a function" with checkbox.attr ? */
      checkbox.checked = true;
      $rootScope.selected_tip_list.push(checkbox.id);
    });

    /*
    console.log("done!");
    console.log($rootScope.selected_tip_list);
    */
    $('#checkall').checked = false;
  };

  $scope.delete_selected = function()
  {
    console.log('Delete selected TO BE IMPLEMENTED');
    console.log($rootScope.selected_tip_list);

     return $http({method: 'PUT', url: '/rtip/operations', data:{
       'operation': 'delete',
       'rtips': $rootScope.selected_tip_list
     }}).
           success(function(data, status, headers, config){ 
             $location.url('/receiver/tips');
             $route.reload();
     });
  };

  $scope.postpone_selected = function()
  {
    console.log('Postpone selected TO BE IMPLEMENTED');
    console.log($rootScope.selected_tip_list);

    return $http({method: 'PUT', url: '/rtip/operations', data:{
      'operation': 'postpone',
      'rtips': $rootScope.selected_tip_list
    }}).
        success(function(data, status, headers, config){
          $location.url('/receiver/tips');
          $route.reload();
        });
  };

  $scope.tip_switch = function (id)
  {
    index_of_tip = $rootScope.selected_tip_list.indexOf(id);
    if (index_of_tip === -1) {
      $rootScope.selected_tip_list.push(id);
    } else {
      $rootScope.selected_tip_list.pop(index_of_tip);
    }
  };

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

