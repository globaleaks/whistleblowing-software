GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', '$location',
function($scope, Authentication, $location) {

  $scope.session_id = sessionStorage['session_id'];
  $scope.auth_landing_page = sessionStorage['auth_landing_page'];
  $scope.role = sessionStorage['role'];

  $scope.logout = Authentication.logout;

  $scope.$watch(function(scope){
    return sessionStorage['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = sessionStorage['session_id'];
    $scope.auth_landing_page = sessionStorage['auth_landing_page'];
    $scope.role = sessionStorage['role'];
  });


}]);

