GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
    flowFile.done = false;
    $scope.uploads.push(flowFile);
  });

  $scope.$on('flow::fileSuccess', function (event, $flow, flowFile) {
    var arrayLength = $scope.uploads.length;
    for (var i = 0; i < arrayLength; i++) {
      if ($scope.uploads[i].uniqueIdentifier == flowFile.uniqueIdentifier) {
        $scope.uploads[i].done = true;
      }
    }
  });
}]);
