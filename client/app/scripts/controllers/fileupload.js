GLClient.controller('WBFileUploadCtrl', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.options = {
    url: '',
    multipart: false,
    headers: Authentication.headers(),
    autoUpload: true,
    maxFileSize: $scope.node.maximum_filesize * 1000 * 1000,
    disableImageResize: false,
    previewMaxWidth: 120,
    previewMaxHeight: 120,
    submit: function (e, data) {
      $(this).fileupload('option', 'url', $scope.fileupload_url);
    }
  }
  if ($scope.fileupload_mode == 'single') {
      $scope.options['maxNumberOfFiles'] = 1
  };
}]);
