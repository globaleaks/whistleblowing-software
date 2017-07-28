GLClient.controller('HomeCtrl', ['$scope', function ($scope) {
  $scope.keycode = '';
}]);

GLClient.controller('ModalCtrl', ['$scope', '$uibModalInstance',
                    function($scope, $uibModalInstance) {
  $scope.ok = function () {
    $uibModalInstance.close();
  };
}]);
