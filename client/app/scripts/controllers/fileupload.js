GLClient.controller('WBFileUploadCtrl', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.options = {
    url: '',
    multipart: false,
    headers: Authentication.headers(),
    autoUpload: true,
    maxFileSize: $scope.node.maximum_filesize * 1024 * 1024,
    submit: function (e, data) {
      $(this).fileupload('option', 'url', $scope.fileupload_url);
    }
  }
  if ($scope.fileupload_mode == 'single') {
      $scope.options['maxNumberOfFiles'] = 1
  };
}]);
controller('FileUploadEditFileController', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.empty_d = true;
  $scope.empty_t = true;
  $scope.file_desc;
  $scope.file_title;
  $scope.edit = function() {
    if ($scope.file_desc) {
      $scope.empty_d = false;
    }
    if ($scope.file_title) {
      $scope.empty_t = false;
    }
  };
}]).
controller('FileDestroyController', ['$scope', 'Authentication', function($scope, Authentication) {
}]);
