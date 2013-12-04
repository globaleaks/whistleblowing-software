GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Node', '$route', '$translate',
function($scope, $rootScope, Authentication, $location,
         Node, $route, $translate) {

  $scope.session_id = $.cookie('session_id');
  $scope.auth_landing_page = $.cookie('auth_landing_page');
  $scope.role = $.cookie('role');
  
  Node.get(function(node_info) {
    if (!$.cookie('language') ||
        $.inArray($.cookie('language'), node_info.languages_enabled == -1)) {
      $.cookie('language', node_info.default_language);
    }

    $rootScope.language = $.cookie('language');
    $rootScope.selected_language = $scope.language;

    var language_count = 0;
    $rootScope.languages_supported = {};
    $rootScope.languages_enabled = {};
    $.each(node_info.languages_supported, function(idx) {
      var code = node_info.languages_supported[idx]['code'];
      $rootScope.languages_supported[code] = node_info.languages_supported[idx]['name'];
      if ($.inArray(code, node_info.languages_enabled) != -1) {
        $rootScope.languages_enabled[code] = node_info.languages_supported[idx]['name'];
        language_count += 1;
      }
    });

    $rootScope.show_language_selector = (language_count > 1);

  });

  $scope.logout = Authentication.logout;

  $rootScope.$watch("language", function() {
    $.cookie('language', $rootScope.language);
    $rootScope.selected_language = $rootScope.language;
    if ($scope.language === undefined) {
        $translate.uses('en');
    } else {
        $translate.uses($scope.language);
    }
    $route.reload();
  });

  $rootScope.$watch("languages_enabled", function() {
    $route.reload();
  });

  $scope.$watch(function(scope) {
    return $.cookie('session_id');
  }, function(newVal, oldVal){
    $scope.session_id = $.cookie('session_id');
    $scope.auth_landing_page = $.cookie('auth_landing_page');
    $scope.role = $.cookie('role');
  });

}]);

