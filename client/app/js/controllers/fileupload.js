GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.disabled = false;

  $scope.$on('flow::fileAdded', function (event, flow, flowFile) {
    $scope.file_error_msg = undefined;
    if (flowFile.size > $scope.node.maximum_filesize * 1024 * 1024) {
      $scope.file_error_msg = "This file exceeds the maximum upload size for this server.";
      event.preventDefault();
    } else {
      if ($scope.field !== undefined && !$scope.field.multi_entry) {
        // if the field allows to load only one file disable the button
        // as soon as a file is loaded.
        $scope.disabled = true;
      }
    }
  });
}]).
controller('ImageUploadCtrl', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http) {
  $scope.imageUploadObj = {};
  $scope.Authentication = $rootScope.Authentication;
  $scope.Utils = $rootScope.Utils;

  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
    $scope.file_error_msg = undefined;
    if (flowFile.size > $rootScope.node.maximum_filesize * 1024 * 1024) {
      $scope.file_error_msg = "This file exceeds the maximum upload size for this server.";
    } else if(flowFile.file.type !== "image/png") {
      $scope.file_error_msg = "Only PNG files are currently supported.";
    }

    console.log($scope.file_error_msg);
    if ($scope.file_error_msg !== undefined)  {
      flowFile.error = true;
      flowFile.error_msg = $scope.file_error_msg;
      event.preventDefault();
    }
  });

  $scope.deletePicture = function() {
    $http({
      method: 'DELETE',
      url: $scope.imageUploadUrl,
      headers: $scope.Authentication.get_headers()
    }).then(function successCallback() {
      $scope.imageUploadModel[$scope.imageUploadModelAttr] = '';
      $scope.imageUploadObj.flow.files = [];
    }, function errorCallback() { });
  };
}]);
