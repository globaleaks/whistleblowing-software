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
  "Utils",
  "arg",
  "confirmFun",
  "cancelFun",
  function ($scope, $uibModalInstance, Utils, arg, confirmFun, cancelFun) {
    $scope.arg = arg;
    $scope.confirmFun = confirmFun;
    $scope.cancelFun = cancelFun;
    $scope.cancel = function () {
      if (arg.objectUrl) {
        URL.revokeObjectURL(arg.objectUrl);
        delete arg.objectUrl;
      }

      return $uibModalInstance.dismiss("cancel");

    };

    var getFileTag = function (type) {
      if (type.indexOf("image/") === 0) {
        return "image";
      } else if (type.indexOf("video/") === 0) {
        return "video";
      } else if (type.indexOf("audio/") === 0) {
        return "audio";
      } else if (type.indexOf("pdf") !== -1) {
        return "pdf";
      } else {
        return "none";
      }
    };

    this.$onInit = function () {
      arg.tag = getFileTag(arg.type);
    };

    Utils.view("api/rfile/" + arg.id, arg.type, function (objectUrl) {
      arg.objectUrl = objectUrl;
      $scope.$digest();
    });
  },
]);
