GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Node', '$route', '$translate',
function($scope, $rootScope, Authentication, $location,
         Node, $route, $translate) {

  if ($rootScope.language) {
    $scope.language = $rootScope.language;
  }

  $scope.session_id = Authentication.id;
  $scope.auth_landing_page = Authentication.auth_landing_page;
  $scope.role = Authentication.role;
 
  Node.get(function(node) {

    if ($rootScope.language == undefined || $.inArray($scope.language, node.languages_enabled) == -1) {
      $rootScope.language = node.default_language;
      $scope.language = node.default_language;
      $translate.uses($scope.language);
    }

    var language_count = 0;
    $rootScope.languages_supported = {};
    $rootScope.languages_enabled = [];
    $rootScope.languages_enabled_selector = [];
    $.each(node.languages_supported, function(idx) {
      var code = node.languages_supported[idx]['code'];
      $rootScope.languages_supported[code] = node.languages_supported[idx]['name'];
      if ($.inArray(code, node.languages_enabled) != -1) {
        $rootScope.languages_enabled[code] = node.languages_supported[idx]['name'];
        $rootScope.languages_enabled_selector.push({"name": node.languages_supported[idx]['name'],"code": code});
        language_count += 1;
      }
    });

    $scope.show_language_selector = (language_count > 1);
  });

  $scope.logout = Authentication.logout;

  $scope.$watch("language", function(newVal, oldVal) {

    if (newVal && newVal !== oldVal) {

      $rootScope.language = $scope.language;

      $translate.uses($scope.language);

      $rootScope.update_node();

      $route.reload();
    }

  });

  $scope.$watch(function(scope) {
    return Authentication.id;
  }, function(newVal, oldVal){
    $scope.session_id = Authentication.id;
    $scope.auth_landing_page = Authentication.auth_landing_page;
    $scope.role = Authentication.role;
  });

  $translate.uses($scope.language);

}]);

