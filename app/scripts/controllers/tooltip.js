GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Translations', 'Node', '$route',
function($scope, $rootScope, Authentication, $location,
         Translations, Node, $route) {

  $scope.session_id = $.cookie('session_id');
  $scope.auth_landing_page = $.cookie('auth_landing_page');
  $scope.role = $.cookie('role');
  
  Node.get(function(node_info) {
    if (!$.cookie('language')) {
      $.cookie('language', node_info.default_language);
    }

    $scope.language = $.cookie('language');
    $rootScope.selected_language = $scope.language;

    var language_count = 0;
    $rootScope.available_languages = {};
    $rootScope.languages_supported = Translations.supported_languages;
    $.each(node_info.languages_enabled, function(idx, lang) {
      $rootScope.available_languages[lang] = Translations.supported_languages[lang];
      language_count += 1;
    });

    $rootScope.show_language_selector = false;
    if (language_count > 1)
      $rootScope.show_language_selector = true;

  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(){
    $.cookie('language', $scope.language);
    $rootScope.selected_language = $scope.language;
    $route.reload();
  });

  $scope.$watch(function(scope){
    return $.cookie('session_id');
  }, function(newVal, oldVal){
    $scope.session_id = $.cookie('session_id');
    $scope.auth_landing_page = $.cookie('auth_landing_page');
    $scope.role = $.cookie('role');
  });

}]);

