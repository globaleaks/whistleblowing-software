GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.disabled = false;

  $scope.onFileAdded = function($event, $file) {
    if ($file.size > $scope.node.maximum_filesize * 1024 * 1024) {
      $file.error = true;
      $file.error_msg = "This file exceeds the maximum upload size for this server.";
      $event.preventDefault();
    } else {
      if ($scope.field !== undefined && !$scope.field.multi_entry) {
        // if the field allows to load only one file disable the button
        // as soon as a file is loaded.
        $scope.disabled = true;
      }
    }
  };
}]);

GLClient.controller('ImageUploadCtrl', ['$scope', '$http', function($scope, $http) {
  $scope.get_auth_headers = $scope.$parent.get_auth_headers;
  $scope.imgDataUri = $scope.$parent.imgDataUri;
  $scope.imageUploadObj = {};

  $scope.deletePicture = function() {
    $http({
      method: 'DELETE',
      url: $scope.imageUploadUrl,
      headers: $scope.get_auth_headers()
    }).then(function successCallback() {
      $scope.imageUploadModel[$scope.imageUploadModelAttr] = '';
      $scope.imageUploadObj.flow.files = [];
    }, function errorCallback() { });
  };
}]);
