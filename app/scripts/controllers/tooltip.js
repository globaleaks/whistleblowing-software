GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', '$location',
function($scope, Authentication, $location) {

  $scope.session_id = sessionStorage['session_id'];
  $scope.auth_landing_page = sessionStorage['auth_landing_page'];
  $scope.user_id = sessionStorage['user_id'];
  $scope.role = sessionStorage['role'];

  $scope.$watch(function(scope){
    return sessionStorage['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = sessionStorage['session_id'];
  });

  $scope.logout = function() {
    Authentication.logout().then(function(){
      $scope.session_id = null;
      sessionStorage.removeItem('session_id');
      $location.path('/login');
    });
  };

}]);

