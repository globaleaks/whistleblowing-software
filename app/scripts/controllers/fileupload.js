GLClient.controller('WBFileUploadCtrlSingle', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.options = {
    url: $scope.fileupload_url,
    multipart: false,
    headers: Authentication.headers(),
    autoUpload: true,
    maxNumberOfFiles: 1,
    maxFileSize: $scope.node.maximum_filesize * 1024 * 1024
  };
}]).
controller('WBFileUploadCtrlMultiple', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.options = {
    url: $scope.fileupload_url,
    multipart: false,
    headers: Authentication.headers(),
    autoUpload: true,
    maxFileSize: $scope.node.maximum_filesize * 1024 * 1024
  };
}]);

