GLClient.controller('MainCtrl', ['$scope', '$rootScope', '$http', '$route', '$routeParams', '$location',  '$translate', 'Node', 'Authentication',
  function($scope, $rootScope, $http, $route, $routeParams, $location, $translate, Node, Authentication) {
    $scope.started = true;

    $scope.custom_stylesheet = '/static/custom_stylesheet.css';
    $scope.logo = '/static/globaleaks_logo.png';

    $scope.update_node = function () {
      Node.get(function (node) {
        $scope.node = node;
        if (!$scope.node.wizard_done && $route.current.$$route.controller != "WizardCtrl") {
          $location.path('/wizard');
        }
      });
    };

    $scope.update = function (model) {
      var success = {};
      success.message = "Updated " + model;
      model.$update(function () {
        if (!$scope.successes) {
          $scope.successes = [];
        }
        $scope.successes.push(success);
      });
    };

    $scope.randomFluff = function () {
      return Math.round(Math.random() * 1000000);
    };

    var refresh = function () {
      $scope.custom_stylesheet = '/static/custom_stylesheet.css?' + $scope.randomFluff();
      $scope.logo = '/static/globaleaks_logo.png?' + $scope.randomFluff();
    };

    $scope.$on("REFRESH", refresh);

    $scope.$on('$routeChangeStart', function (next, current) {
      $scope.update_node();
    });

    $scope.update_node();

    $scope.isWizard = function () {
      return $location.path() == '/wizard';
    };

    $scope.isHomepage = function () {
      return $location.path() == '/';
    };

    $scope.isLoginPage = function () {
      return $location.path() == '/login';
    };

    $scope.showLoginForm = function () {
      return (!$scope.isHomepage() &&
              !$scope.isLoginPage());
    }

    $scope.hasSubtitle = function () {
      return $scope.header_subtitle != '';
    }

    var refresh = function () {

      $scope.session_id = Authentication.id;
      $scope.auth_landing_page = Authentication.auth_landing_page;
      $scope.role = Authentication.role;

      Node.get(function (node) {

        if ($rootScope.language == undefined || $.inArray($rootScope.language, node.languages_enabled) == -1) {
          $rootScope.language = node.default_language;
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

      $translate.use($rootScope.language);

      $route.reload();

    };

    $scope.$on('$routeChangeSuccess', function() {
      if($routeParams.lang) {
        $rootScope.language = $scope.language = $routeParams.lang;
      }
    });

    $scope.$on("REFRESH", refresh);

    $rootScope.$watch('language', function (newVal, oldVal) {

      if (newVal && newVal !== oldVal) {

        $translate.use($rootScope.language);

        if (newVal != "ar") {
          $scope.build_stylesheet = "/styles.css";
        } else {
          $scope.build_stylesheet = "/styles-rtl.css";
        }

        $scope.update_node();

        $route.reload();
      }

    });

    $scope.$watch(function (scope) {
      return Authentication.id;
    }, function (newVal, oldVal) {
      $scope.session_id = Authentication.id;
      $scope.auth_landing_page = Authentication.auth_landing_page;
      $scope.role = Authentication.role;
    });

    refresh();
  }

]);

GLClient.controller('ModalCtrl', ['$scope', 
  function($scope, $modalInstance, error) {
    $scope.error = error;
    $scope.seconds = error.arguments[0];
}]);

TabCtrl = ['$scope', function($scope) {
  /* Empty controller function used to implement TAB pages */
}];

GLClient.controller('DisableEncryptionCtrl', ['$scope', '$modalInstance', function($scope, $modalInstance){
    $scope.close = function() {
      $modalInstance.close(false);
    };

    $scope.no = function() {
      $modalInstance.close(false);
    };
    $scope.ok = function() {
      $modalInstance.close(true);
    };

}]);

angular.module('GLClient.fileuploader', ['blueimp.fileupload'])
  .config(['$httpProvider', 'fileUploadProvider',
    function ($httpProvider, fileUploadProvider) {
      delete $httpProvider.defaults.headers.common['X-Requested-With'];
      angular.extend(fileUploadProvider.defaults, {
        multipart: false,
      });
    }
]);

