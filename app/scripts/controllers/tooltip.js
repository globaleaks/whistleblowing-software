GLClient.controller('toolTipCtrl',
  ['$scope', '$rootScope', '$routeParams', '$route', '$translate', 
    'Authentication', 'Node',
  function($scope, $rootScope, $routeParams, $route, $translate,
           Authentication, Node) {

  if($routeParams.lang) {
    $rootScope.language = $scope.language = $routeParams.lang;
  }
  
  var refresh = function () {

    $scope.session_id = Authentication.id;
    $scope.auth_landing_page = Authentication.auth_landing_page;
    $scope.role = Authentication.role;

    Node.get(function (node) {

      if ($rootScope.language == undefined || $.inArray($rootScope.language, node.languages_enabled) == -1) {
        $rootScope.language = $scope.language = node.default_language;
      }

      var language_count = 0;
      $scope.languages_supported = {};
      $scope.languages_enabled = [];
      $scope.languages_enabled_selector = [];
      $.each(node.languages_supported, function (idx) {
        var code = node.languages_supported[idx]['code'];
        $scope.languages_supported[code] = node.languages_supported[idx]['name'];
        if ($.inArray(code, node.languages_enabled) != -1) {
          $scope.languages_enabled[code] = node.languages_supported[idx]['name'];
          $scope.languages_enabled_selector.push({"name": node.languages_supported[idx]['name'], "code": code});
          language_count += 1;
        }
      });

      $scope.show_language_selector = (language_count > 1);
    });

    $translate.use($scope.language);
  };

  $scope.$on("REFRESH", refresh);

  $scope.$watch("language", function(newVal, oldVal) {

    if (newVal && newVal !== oldVal) {

      $rootScope.language = $scope.language;

      $translate.use($scope.language);

      if (newVal != "ar") {
        $rootScope.build_stylesheet = "/styles.css";
      } else {
        $rootScope.build_stylesheet = "/styles-rtl.css";
      }

      $scope.update_node();

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
GLClient.controller('ModalCtrl', ['$scope', '$location', '$modalInstance', 'error',
                    function ($scope, $location, $modalInstance, error){
    $scope.error = error;
    $scope.seconds = error.arguments[0];

    $scope.close = function() {
      $modalInstance.dismiss('cancel'); 
    };
}]);
