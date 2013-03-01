GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', '$location', '$cookies',
function($scope, Authentication, $location, $cookies) {

  $scope.session_id = $cookies['session_id'];
  $scope.auth_landing_page = $cookies['auth_landing_page'];
  $scope.role = $cookies['role'];

  $scope.logout = Authentication.logout;

  $scope.$watch(function(scope){
    return $cookies['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = $cookies['session_id'];
    $scope.auth_landing_page = $cookies['auth_landing_page'];
    $scope.role = $cookies['role'];
  });


}]);

