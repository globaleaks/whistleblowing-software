GLClient.controller('TipCtrl', ['$rootScope', '$scope', '$http', '$route', '$location', '$modal',
  function($rootScope, $scope, $http, $route, $location, $modal) {

  $scope.selected_tips = 0;

  $scope.tipall = function ()
  {
    $rootScope.selected_tip_list = [];
    $('.checkboxes').each(function (i, checkbox) {
      checkbox.checked = true;
      $rootScope.selected_tip_list.push(checkbox.id);
    });

    /* bug: this set is getting ignored, probably because is bound to ng-click */
    $('#checkall').checked = false;
    $scope.selected_tips = $rootScope.selected_tip_list.length;
  };

  $scope.delete_selected = function()
  {
    if ($scope.selected_tips === 0) {
      alert("nop");
    } else {

      return $http({method: 'PUT', url: '/rtip/operations', data:{
        'operation': 'delete',
        'rtips': $rootScope.selected_tip_list
      }}).
          success(function(data, status, headers, config){
            $rootScope.selected_tip_list = [];
            $location.url('/receiver/tips');
            $route.reload();
          });
    }
  };

  $scope.postpone_selected = function()
  {
    if ($scope.selected_tips === 0) {
      alert("nop");
    } else {

      return $http({method: 'PUT', url: '/rtip/operations', data:{
        'operation': 'postpone',
        'rtips': $rootScope.selected_tip_list
      }}).
         success(function(data, status, headers, config){
           $rootScope.selected_tip_list = [];
           $location.url('/receiver/tips');
           $route.reload();
         });
    }
  };

  $scope.tip_switch = function (id)
  {
    checkbox_element = $("#"+id);
    checkbox_element.checked = !checkbox_element.checked;

    $rootScope.selected_tip_list = [];
    $('.checkboxes').each(function (i, checkbox) {
      if(checkbox.checked) {
        $rootScope.selected_tip_list.push(checkbox.id);
      }
    });
    $scope.selected_tips = $rootScope.selected_tip_list.length;
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

