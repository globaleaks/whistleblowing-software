GLClient.controller('ReceiverSidebarCtrl', ['$scope', '$location', function($scope, $location){
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";
}]).
controller('ReceiverTipsCtrl', ['$scope',  '$http', '$route', '$location', '$uibModal', 'FileSaver', 'Blob', 'ReceiverTips',
  function($scope, $http, $route, $location, $uibModal, FileSaver, Blob, ReceiverTips) {
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

  $scope.getTip = function(tip) {
    $http({
      method: 'GET',
      url: '/rtip/' + tip.id + '/export',
      responseType: 'blob',
    }).then(function (response) {
      var blob = response.data;
      //blob = new Blob(["This array should be non empty in this.result"]);
      f = new FileReader();
      f.onload = function(progressEvent) {
      // onload is specified here: https://w3c.github.io/FileAPI/#APIASynch
        var buf = this.result; // Tears occur at this moment. Buf is empty
        console.log(buf);
        var digest = openpgp.crypto.hash.sha512(buf);
        console.log(digest);
        digest = openpgp.crypto.hash.sha512(new Uint8Array());
        console.log(digest);
      };
      f.readAsArrayBuffer(blob);
      //FileSaver.saveAs(blob, "Drink-More-Pepsi.zip"); 
    }, function(fail) {
      console.log(fail); 
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

    return $http({method: 'PUT', url: '/rtip/operations', data:{
      'operation': $scope.operation,
      'rtips': $scope.selected_tips
    }}).success(function(){
      $scope.selected_tips = [];
      $route.reload();
    });
  };
}]);
