GLClient.controller('CustodianIdentityAccessRequestsCtrl', ['$scope',  '$http', '$route',  '$uibModal', 'IdentityAccessRequests',
  function($scope, $http, $route, $uibModal, IdentityAccessRequests) {
  $scope.iars = IdentityAccessRequests.query();

  $scope.authorize_identity_access_request = function (iar_id) {
    return $http.put('custodian/identityaccessrequest/' + iar_id, {'reply': 'authorized', 'reply_motivation': ''}).
      then(function(){
        $route.reload();
      });
  };

  $scope.file_denied_identity_access_reply = function (iar_id) {
    $uibModal.open({
      templateUrl: 'views/partials/tip_operation_file_identity_access_reply.html',
      controller: 'IdentityAccessReplyCtrl',
      resolve: {
        iar: function () {
          return iar_id;
        }
      }
    });
  };
}]).
controller('IdentityAccessReplyCtrl', ['$scope', '$http', '$route', '$uibModalInstance', 'iar',
  function ($scope, $http, $route, $uibModalInstance, iar) {
    $scope.iar = iar;
    $scope.cancel = function () {
      $uibModalInstance.close();
    };

    $scope.ok = function () {
      $uibModalInstance.close();
      return $http.put('custodian/identityaccessrequest/' + $scope.iar, {'reply': 'denied', 'reply_motivation': $scope.reply_motivation}).
        then(function(){
          $route.reload();
        });
    };
}]);
