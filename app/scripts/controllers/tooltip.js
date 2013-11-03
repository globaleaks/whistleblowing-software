GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Node', '$route', '$translate',
function($scope, $rootScope, Authentication, $location,
         Node, $route, $translate) {

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
    $rootScope.available_languages = {}
    $rootScope.languages_supported = node_info.languages_enabled;
    $.each(node_info.languages_supported, function(idx) {
      if ($.inArray(node_info.languages_supported[idx]['code'], node_info.languages_enabled) != -1) {
        var code = node_info.languages_supported[idx]['code'];
        var name = node_info.languages_supported[idx]['name'];
        $rootScope.available_languages[code] = name;
        language_count += 1;
      }
    });

    $rootScope.show_language_selector = false;
    if (language_count > 1)
      $rootScope.show_language_selector = true;

  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(){
    $.cookie('language', $scope.language);
    $rootScope.selected_language = $scope.language;
    if ($scope.language === undefined) {
        $translate.uses('en');
    } else {
        $translate.uses($scope.language);
    }
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

