GL.controller("ReceiptCtrl", ["$scope", function($scope) {
  $scope.formatted_receipt = $scope.Utils.format_receipt($scope.receipt);
}]);
