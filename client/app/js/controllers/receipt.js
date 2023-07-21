GL.controller("ReceiptCtrl", ["$scope", function($scope) {
  $scope.formatted_receipt = function(receipt) {
    if (!receipt || receipt.length !== 16) {
      return "";
    }

    return receipt.substring(0, 4) + " " +
           receipt.substring(4, 4) + " " +
           receipt.substring(8, 4) + " " +
           receipt.substring(12, 4);
  }($scope.receipt);
}]);
