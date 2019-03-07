GLClient.controller("ReceiptController", ["$scope", "Authentication",
  function($scope, Authentication) {
    var format_receipt = function(receipt) {
      if (!receipt || receipt.length !== 16) {
        return "";
      }

      return receipt.substr(0, 4) + " " +
             receipt.substr(4, 4) + " " +
             receipt.substr(8, 4) + " " +
             receipt.substr(12, 4);
    };

    if (Authentication.submission) {
      $scope.receipt = Authentication.submission.receipt;
      $scope.formatted_receipt = format_receipt($scope.receipt);
    }
}]);
