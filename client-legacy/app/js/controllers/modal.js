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
      return $uibModalInstance.dismiss("cancel");

    };

    var getFileTag = function (type) {
      if (type === "application/pdf") {
        return "pdf";
      } else if (type.indexOf("audio/") === 0) {
        return "audio";
      } else if (type.indexOf("image/") === 0) {
        return "image";
      } else if (type === "text/csv" || type === "text/plain") {
        return "txt";
      } else if (type.indexOf("video/") === 0) {
        return "video";
      } else {
        return "none";
      }
    };

    this.$onInit = function () {
      arg.tag = getFileTag(arg.type);
      // setting iframe height to 75% of window height if tag is pdf
      arg.iframeHeight =  window.innerHeight * 0.75;
    };

    Utils.view("api/recipient/wbfiles/" + arg.id, arg.type, function (blob) {
      arg.loaded = true;
      $scope.$apply();

      window.addEventListener("message", function() {
        var data = {
          tag: arg.tag,
          blob: blob
        };
        angular.element(document.querySelector("#viewer"))[0].contentWindow.postMessage(data, "*");
      }, {once: true});
    });
  },
]);
