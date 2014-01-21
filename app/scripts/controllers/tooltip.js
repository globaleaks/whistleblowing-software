GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', 'Authentication',
   '$location', 'Node', '$route', '$translate',
function($scope, $rootScope, Authentication, $location,
         Node, $route, $translate) {

  var refresh = function() {

    $scope.session_id = Authentication.id;
    $scope.auth_landing_page = Authentication.auth_landing_page;
    $scope.role = Authentication.role;
    $scope.logout = Authentication.logout;

    Node.get(function(node) {

      if ($rootScope.language == undefined || $.inArray($rootScope.language, node.languages_enabled) == -1) {
        $scope.language = node.default_language;
        $rootScope.language = node.default_language;
      }

      var language_count = 0;
      $scope.languages_supported = {};
      $scope.languages_enabled = [];
      $scope.languages_enabled_selector = [];
      $.each(node.languages_supported, function(idx) {
        var code = node.languages_supported[idx]['code'];
        $scope.languages_supported[code] = node.languages_supported[idx]['name'];
        if ($.inArray(code, node.languages_enabled) != -1) {
          $scope.languages_enabled[code] = node.languages_supported[idx]['name'];
          $scope.languages_enabled_selector.push({"name": node.languages_supported[idx]['name'],"code": code});
          language_count += 1;
        }
      });

      $scope.show_language_selector = (language_count > 1);
    });

    $translate.uses($scope.language);
  }

  $scope.$on("REFRESH", refresh);

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

  refresh();

}]);

