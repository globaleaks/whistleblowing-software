GLClient.controller('CustodianIdentityAccessRequestsCtrl', ['$scope',  '$http', '$route', '$location', '$modal', 'IdentityAccessRequests',
  function($scope, $http, $route, $location, $modal, IdentityAccessRequests) {
  $scope.iars = IdentityAccessRequests.query();

  $scope.authorize_identity_access_request = function (iar_id) {
    return $http.put('/custodian/identityaccessrequest/' + iar_id, {'reply': 'authorized', 'reply_motivation': ''}).
      success(function(data, status, headers, config){
        $route.reload();
      });
  };

  $scope.file_denied_identity_access_reply = function (iar_id) {
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/tip_operation_file_identity_access_reply.html',
      controller: IdentityAccessReplyCtrl,
      resolve: {
        iar: function () {
          return iar_id;
        }
      }
    });
  };
}]);

IdentityAccessReplyCtrl = ['$scope', '$http', '$route', '$modalInstance', 'iar',
  function ($scope, $http, $route, $modalInstance, iar) {
    $scope.iar = iar;
    $scope.cancel = function () {
      $modalInstance.close();
    };

    $scope.ok = function () {
      $modalInstance.close();
      return $http.put('/custodian/identityaccessrequest/' + $scope.iar, {'reply': 'denied', 'reply_motivation': $scope.reply_motivation}).
        success(function(data, status, headers, config){
          $route.reload();
        });
    };
}];