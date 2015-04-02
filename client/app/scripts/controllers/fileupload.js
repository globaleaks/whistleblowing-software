GLClient.controller('WBFileUploadCtrl', ['$scope', 'Authentication', function($scope, Authentication) {
  $scope.auth_headers = Authentication.headers()
}]);
