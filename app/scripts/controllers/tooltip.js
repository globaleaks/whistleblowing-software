GLClient.controller('toolTipCtrl',
  ['$scope', 'Authentication', '$location', '$cookies', 'Translations',
function($scope, Authentication, $location, $cookies, Translations) {
  if (!$cookies['language'])
    $cookies['language'] = 'en';

  $scope.session_id = $cookies['session_id'];
  $scope.auth_landing_page = $cookies['auth_landing_page'];
  $scope.role = $cookies['role'];
  $scope.language = $cookies['language'];
  $scope.supported_languages = Translations.supported_languages;

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

