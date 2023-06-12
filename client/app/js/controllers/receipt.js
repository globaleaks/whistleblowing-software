GL.controller("ReceiptCtrl", ["$scope", function($scope) {
  $scope.formatted_receipt = function(receipt) {
    if (!receipt || receipt.length !== 16) {
      return "";
    }

    return receipt.substr(0, 4) + " " +
           receipt.substr(4, 4) + " " +
           receipt.substr(8, 4) + " " +
           receipt.substr(12, 4);
  }($scope.receipt);
}]);
