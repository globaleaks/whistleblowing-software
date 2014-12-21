GLClient.controller('WBFileUploadCtrl', ['$scope', 'Authentication', function($scope, Authentication) {
  if ($scope.fileupload_mode == undefined || $scope.fileupload_mode == 'multiple') {
    $scope.options = {
      url: $scope.fileupload_url,
      multipart: false,
      headers: Authentication.headers(),
      autoUpload: true,
      maxFileSize: $scope.node.maximum_filesize * 1024 * 1024
    };
  } else { // 'single'
    $scope.options = {
      url: $scope.fileupload_url,
      multipart: false,
      headers: Authentication.headers(),
      autoUpload: true,
      maxFileSize: $scope.node.maximum_filesize * 1024 * 1024,
      maxNumberOfFiles: 1
    };
  }
}]);
