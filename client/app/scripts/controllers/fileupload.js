GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {

  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {

    flowFile.done = false;
    $scope.uploads.push(flowFile);

    if (flowFile.size > $scope.node.maximum_filesize * 1024 * 1024) {
      flowFile.error = true;
      flowFile.error_msg = "This file exceeds the maximum upload size for this server.";
      flowFile.done = true;
      event.preventDefault();
    }

    angular.forEach($scope.upload_callbacks, function (callback) {
      callback();
    });
  });

  $scope.$on('flow::fileSuccess', function (event, $flow, flowFile) {
    var arrayLength = $scope.uploads.length;
    for (var i = 0; i < arrayLength; i++) {
      if ($scope.uploads[i].uniqueIdentifier === flowFile.uniqueIdentifier) {
        $scope.uploads[i].done = true;
      }
    }

    angular.forEach($scope.upload_callbacks, function (callback) {
      callback();
    });

  });
}]);
