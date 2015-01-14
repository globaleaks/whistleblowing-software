GLClient.controller('MainCtrl', ['$scope', '$rootScope', '$http', '$route', '$routeParams', '$location',  '$translate', 'Authentication', 'Node', 'GLCache',
  function($scope, $rootScope, $http, $route, $routeParams, $location, $translate, Authentication, Node, GLCache) {
    $scope.started = true;

    $scope.custom_stylesheet = '/static/custom_stylesheet.css';
    $scope.logo = '/static/globaleaks_logo.png';

    $scope.update_node = function () {
      $scope.node = Node.get(function (node) {
        if (!$scope.node.wizard_done && $route.current.$$route.controller != "WizardCtrl") {
          $location.path('/wizard');
        }
      });
    };

    $scope.update = function (model, cb, errcb) {
      var success = {};
      success.message = "Updated " + model;
      model.$update(function(result) {
        if (!$scope.successes) {
          $scope.successes = [];
        }
        $scope.successes.push(success);
      }).then(
        function() { if (cb != undefined) cb(); },
        function() { if (errcb != undefined) errcb(); }
      );
    };

    $scope.randomFluff = function () {
      return Math.round(Math.random() * 1000000);
    };

    $scope.isWizard = function () {
      return $location.path() == '/wizard';
    };

    $scope.isHomepage = function () {
      return $location.path() == '/';
    };

    $scope.isLoginPage = function () {
      return ($location.path() == '/login' ||
              $location.path() == '/admin');
    };

    $scope.showLoginForm = function () {
      return (!$scope.isHomepage() &&
              !$scope.isLoginPage());
    }

    $scope.hasSubtitle = function () {
      return $scope.header_subtitle != '';
    }

    var init = function () {

      $scope.custom_stylesheet = '/static/custom_stylesheet.css?' + $scope.randomFluff();
      $scope.logo = '/static/globaleaks_logo.png?' + $scope.randomFluff();

      $scope.session_id = Authentication.id;
      $scope.homepage = Authentication.homepage;
      $scope.auth_landing_page = Authentication.auth_landing_page;
      $scope.role = Authentication.role;

      $scope.node = Node.get(function (node) {

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

    };

    $scope.$on('$routeChangeSuccess', function() {
      if($location.search().lang) {
        $rootScope.language = $scope.language = $location.search().lang;
      }
    });

    $scope.$on("REFRESH", function() {
      GLCache.removeAll();
      init();
      $route.reload();
    });

    $rootScope.$watch('language', function (newVal, oldVal) {

      if (newVal && newVal !== oldVal) {

        if(oldVal === undefined && newVal === $scope.node.default_language)
          return;

        $translate.use($rootScope.language);

        if (newVal != "ar" && newVal != "he") {
          $scope.build_stylesheet = "/styles.css";
        } else {
          $scope.build_stylesheet = "/styles-rtl.css";
        }

        $rootScope.$broadcast("REFRESH");

      }

    });

    $scope.$watch(function (scope) {
      return Authentication.id;
    }, function (newVal, oldVal) {
      $scope.session_id = Authentication.id;
      $scope.homepage = Authentication.homepage;
      $scope.auth_landing_page = Authentication.auth_landing_page;
      $scope.role = Authentication.role;
    });

    init();
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

