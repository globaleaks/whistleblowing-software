GLClient.controller('PrivacyBadgeBoxCtrl', ['$scope', function($scope) {

    $scope.showBox = function () {
      $scope.displayBox = true;
      $scope.boxes = 'open';
    }

    $scope.hideBox = function() {
      $scope.displayBox = false;
      $scope.boxes = 'closed';
    }

    $scope.displayBox = true;
    $scope.boxes = 'open';

}]);
