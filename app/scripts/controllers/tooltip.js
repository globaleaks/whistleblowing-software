GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', '$location', '$cookies',
function($scope, Authentication, $location, $cookies) {

  $scope.session_id = $cookies['session_id'];
  $scope.auth_landing_page = $cookies['auth_landing_page'];
  $scope.role = $cookies['role'];
  $scope.language = $cookies['language'];
  $scope.supported_languages = translations.supported_languages;

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(){
    $cookies['language'] = $scope.language;
  });

  $scope.$watch(function(scope){
    return $cookies['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = $cookies['session_id'];
    $scope.auth_landing_page = $cookies['auth_landing_page'];
    $scope.role = $cookies['role'];
  });

}]);

