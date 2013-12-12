GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Node', '$route', '$translate',
function($scope, $rootScope, Authentication, $location,
         Node, $route, $translate) {

  application_default_lang = 'en';

  if ($.cookie('language')) {
    $scope.language = $.cookie('language');
  } else {
    $scope.language = application_default_lang;
  }

  $scope.session_id = $.cookie('session_id');
  $scope.auth_landing_page = $.cookie('auth_landing_page');
  $scope.role = $.cookie('role');
 
  Node.get(function(node) {
    if ($.inArray($scope.language, node.languages_enabled) == -1) {
      $.cookie('language', node.default_language);  
      $scope.language = node.default_language;
      $translate.uses($scope.language);
    }

    var language_count = 0;
    $rootScope.languages_supported = {};
    $rootScope.languages_enabled = {};
    $.each(node.languages_supported, function(idx) {
      var code = node.languages_supported[idx]['code'];
      $rootScope.languages_supported[code] = node.languages_supported[idx]['name'];
      if ($.inArray(code, node.languages_enabled) != -1) {
        $rootScope.languages_enabled[code] = node.languages_supported[idx]['name'];
        language_count += 1;
      }
    });

    $scope.show_language_selector = (language_count > 1);
  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(newVal, oldVal) {

    if (newVal && newVal !== oldVal) {

      $.cookie('language', $scope.language);

      $translate.uses($scope.language);

      $rootScope.update_node();

      $route.reload();
    }

  });

  $scope.$watch(function(scope) {
    return $.cookie('session_id');
  }, function(newVal, oldVal){
    $scope.session_id = $.cookie('session_id');
    $scope.auth_landing_page = $.cookie('auth_landing_page');
    $scope.role = $.cookie('role');
  });

  $translate.uses($scope.language);

}]);

