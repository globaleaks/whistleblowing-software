GL.controller("CustodianIdentityAccessRequestsCtrl", ["$scope", "$http", "$uibModal", "IdentityAccessRequests",
  function($scope, $http, $uibModal, IdentityAccessRequests) {
  $scope.iars = IdentityAccessRequests.query();

  $scope.authorize_identity_access_request = function (iar_id) {
    return $http.put("api/custodian/iars/" + iar_id, {"reply": "authorized", "reply_motivation": ""}).
      then(function(){
        $scope.reload();
      });
  };

  $scope.file_denied_identity_access_reply = function (iar_id) {
    $uibModal.open({
      templateUrl: "views/modals/tip_operation_file_identity_access_reply.html",
      controller: "IdentityAccessReplyCtrl",
      resolve: {
        iar: function () {
          return iar_id;
        }
      }
    });
  };
}]).
controller("IdentityAccessReplyCtrl", ["$scope", "$http", "$uibModalInstance", "iar",
  function ($scope, $http, $uibModalInstance, iar) {
    $scope.iar = iar;
    $scope.cancel = function () {
      $uibModalInstance.close();
    };

    $scope.confirm = function () {
      $uibModalInstance.close();
      return $http.put("api/custodian/iars/" + $scope.iar, {"reply": "denied", "reply_motivation": $scope.reply_motivation}).
        then(function(){
          $scope.reload();
        });
    };
}]);
