GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.disabled = false

  $scope.onFileAdded = function($event, $file, $flow) {
    if ($file.size > $scope.node.maximum_filesize * 1024 * 1024) {
      $file.error = true;
      $file.error_msg = "This file exceeds the maximum upload size for this server.";
      event.preventDefault();
    } else {
      if ($scope.field !== undefined && !$scope.field.multi_entry) {
        $scope.disabled = true;
      }
    }
  };
}]);
