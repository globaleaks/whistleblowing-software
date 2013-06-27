GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', '$cookies', 'Translations', 'Node',
function($scope, $rootScope, Authentication, $location,
         $cookies, Translations, Node) {
  if (!$cookies['language'])
    $cookies['language'] = 'en';

  $scope.session_id = $cookies['session_id'];
  $scope.auth_landing_page = $cookies['auth_landing_page'];
  $scope.role = $cookies['role'];
  $scope.language = $cookies['language'];

  Node.get(function(node_info) {
    $scope.supported_languages = {};
    $.each(node_info.languages_supported, function(idx, lang){
      $scope.supported_languages[lang.code] = lang.name;
    });
  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(){
    $cookies['language'] = $scope.language;
    $rootScope.selected_language = $scope.language;
  });

  $scope.$watch(function(scope){
    return $cookies['session_id'];
  }, function(newVal, oldVal){
    $scope.session_id = $cookies['session_id'];
    $scope.auth_landing_page = $cookies['auth_landing_page'];
    $scope.role = $cookies['role'];
  });

}]);

