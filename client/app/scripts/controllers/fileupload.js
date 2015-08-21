GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
    $scope.uploads.push(flowFile);

    if (flowFile.size > $scope.node.maximum_filesize * 1024 * 1024) {
      flowFile.error = true;
      flowFile.error_msg = "This file exceeds the maximum upload size for this server.";
      event.preventDefault();
    }
  });
}]);
