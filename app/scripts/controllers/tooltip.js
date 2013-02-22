GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', function($scope, Authentication) {

  $scope.session_id = sessionStorage['session_id'];
  $scope.auth_landing_page = sessionStorage['auth_landing_page'];
  $scope.user_id = sessionStorage['user_id'];
  $scope.role = sessionStorage['role'];

  $scope.logout = function() {
    Authentication.logout().then(function(){
      $scope.session_id = null;
      sessionStorage.removeItem('session_id');
      $location.path('/login');
    });
  };

}]);

