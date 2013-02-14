GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', function($scope, Authentication) {

  $scope.session_id = sessionStorage['session_id'];

  $scope.logout = function() {
    Authentication.logout().then(function(){
      $scope.session_id = null;
      sessionStorage.removeItem('session_id');
      $location.path('/login');
    });
  };

}]);

