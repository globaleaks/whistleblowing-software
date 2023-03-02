GL.
controller("ConfirmableModalCtrl",
           ["$scope", "$uibModalInstance", "arg", "confirmFun", "cancelFun", function($scope, $uibModalInstance, arg, confirmFun, cancelFun) {
  $scope.arg = arg;
  $scope.confirmFun = confirmFun;
  $scope.cancelFun = cancelFun;

  $scope.confirm = function(result) {
    if ($scope.confirmFun) {
      $scope.confirmFun(result);
    }

    return $uibModalInstance.close(result);
  };

  $scope.cancel = function(result) {
    if ($scope.cancelFun) {
      $scope.cancelFun(result);
    }

    return $uibModalInstance.dismiss("cancel");
    };
}]).controller("ViewModalCtrl", [
  "$scope",
  "$uibModalInstance",
  "arg",
  "confirmFun",
  "cancelFun",
  function ($scope, $uibModalInstance, arg, confirmFun, cancelFun) {
    $scope.arg = arg;
    $scope.confirmFun = confirmFun;
    $scope.cancelFun = cancelFun;
    $scope.cancel = function () {
      return $uibModalInstance.dismiss("cancel");
    };
  },
]);
