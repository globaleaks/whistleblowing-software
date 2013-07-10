GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', '$cookies', 'Translations', 'Node', '$route',
function($scope, $rootScope, Authentication, $location,
         $cookies, Translations, Node, $route) {
  if (!$cookies['language'])
    $cookies['language'] = 'en';

  $scope.session_id = $cookies['session_id'];
  $scope.auth_landing_page = $cookies['auth_landing_page'];
  $scope.role = $cookies['role'];
  $scope.language = $cookies['language'];
  $rootScope.selected_language = $scope.language;
  
  Node.get(function(node_info) {
    $rootScope.available_languages = {};
    $rootScope.languages_supported = Translations.supported_languages;
    $.each(node_info.languages_enabled, function(idx, lang) {
      $rootScope.available_languages[lang] = Translations.supported_languages[lang];
    });
  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(){
    $cookies['language'] = $scope.language;
    $route.reload();
  });

  $scope.$watch(function(scope){
    return $cookies['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = $cookies['session_id'];
    $scope.auth_landing_page = $cookies['auth_landing_page'];
    $scope.role = $cookies['role'];
  });

}]);

