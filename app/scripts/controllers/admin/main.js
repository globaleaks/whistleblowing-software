function CollapseDemoCtrl($scope) {
  $scope.isCollapsed = false;
}

GLClient.controller('AdminCtrl',
    ['$rootScope', '$scope', '$http', '$route', '$location', 'Admin',
function($rootScope, $scope, $http, $route, $location, Admin) {

  // XXX this should actually be defined per controller
  // otherwise every time you open a new page the button appears enabled
  // because such item is !=
  $scope.master = {};

  // XXX convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.admin = new Admin();

  $scope.languages_enabled_edit = {};
  $scope.languages_default_selector = {};

  function CollapseLanguages($scope) {
    $scope.isCollapsed = false;
  }

  $rootScope.$watch('languages_enabled', function(){
    if ($rootScope.languages_enabled) {
      $scope.languages_default_selector = {};
      $.each($rootScope.languages_supported, function(lang){
        if (lang in $rootScope.languages_enabled) {
          $scope.languages_enabled_edit[lang] = true;
        } else {
          $scope.languages_enabled_edit[lang] = false;
        }
      });
    }

  }, true);

  $scope.$watch('languages_enabled_edit', function() {
    if ($rootScope.languages_enabled) {
      var languages_default_selector = {};
      var change_default = false;
      var language_selected = $scope.admin.node.default_language;
      if (! $scope.languages_enabled_edit[$scope.admin.node.default_language]) {
        change_default = true;
      }

      $.each($rootScope.languages_supported, function(lang) {
        if ($scope.languages_enabled_edit[lang]) {
          languages_default_selector[lang] = $scope.languages_supported[lang];

          if (change_default === true) {
            language_selected = lang;
            change_default = false;
          }
        }
      });

      $scope.admin.node.default_language = language_selected;
      $scope.languages_default_selector = languages_default_selector;

    }
  }, true);

  // We need to have a special function for updating the node since we need to add old_password and password attribute
  // if they are not present
  $scope.updateNode = function(node) {

    if (node.password === undefined)
      node.password = "";
    if (node.check_password === undefined)
      node.password = "";
    if (node.old_password === undefined)
      node.old_password = "";

    var languages_enabled = [];
    $.each($scope.languages_enabled_edit, function(lang, enabled) {
      if (enabled) {
        languages_enabled.push(lang);
      }
    });

    node.languages_enabled = languages_enabled;

    var language_count = 0;
    languages_enabled = {};

    $.each(node.languages_supported, function(idx) {
      var code = node.languages_supported[idx]['code'];
      if ($.inArray(code, node.languages_enabled) != -1) {
        languages_enabled[code] = node.languages_supported[idx]['name'];
        language_count += 1;
      }
    });

    $rootScope.languages_enabled = languages_enabled;
    $rootScope.show_language_selector = (language_count > 1);

    if ($.inArray($rootScope.language, node.languages_enabled) == -1) {
      $rootScope.language = node.default_language;
    }

    $scope.update(node);

    $rootScope.update_node();

    $route.reload();
  }

  $scope.update = function(model) {
    var success = {};
    success.message = "Updated " + model;
    model.$update(function(){
      if (!$rootScope.successes) {
        $rootScope.successes = [];
      };
      $rootScope.successes.push(success);
    });
  };

}]);

GLClient.controller('AdminPasswordCtrl', ['$scope', 'changePasswordWatcher',
                    function($scope, changePasswordWatcher) {
    changePasswordWatcher($scope, "admin.node.old_password",
        "admin.node.password", "admin.node.check_password");
}]);

GLClient.controller('AdminAdvancedCtrl', ['$scope', 'changeParamsWatcher',
                    function($scope, changeParamsWatcher) {
    changeParamsWatcher($scope);
}]);

GLClient.controller('FileUploadCtrl', ['$scope', '$http', function($scope, $http){
    $scope.uploadfile = false;

    $scope.fileSelected = false;
    $scope.markFileSelected = function() {
      $scope.fileSelected = true;
    }

    $scope.openUploader = function() {
      $scope.uploadfile = true;
    }

    $scope.closeUploader = function() {
      $scope.uploadfile = $scope.fileSelected = false;
    }

    $scope.customCSSUrl = function() {
      return "/admin/staticfiles/custom_stylesheet";
    }

    $scope.customCSSReloadUrl = function() {
      return "/static" + "custom_stylesheet?" + $scope.randomFluff;
    }

    $scope.receiverImgUrl = function() {
      return "/admin/staticfiles/" + $scope.receiver.receiver_gus;
    }

    $scope.receiverImgReloadUrl = function() {
      return "/static/" + $scope.receiver.receiver_gus + ".png?" + $scope.randomFluff;
    }

}]);

GLClient.controller('AdminContentCtrl', ['$scope', '$http', 'StaticFiles', function($scope, $http, StaticFiles){
  $scope.tabs = [
    {
      title:"Main Configuration",
      template: "views/admin/content/tab1.html",
      ctrl: TabCtrl
    },
    {
      title:"Theme Customization",
      template: "views/admin/content/tab2.html",
      ctrl: TabCtrl
    },
    {
      title: "Translation Customization",
      template: "views/admin/content/tab3.html",
      ctrl: TabCtrl
    }
  ];

  $scope.update_static_files = function() {
    var updated_staticfiles = StaticFiles.query(function() {
      $scope.staticfiles = updated_staticfiles;
    });
  }

  $scope.uploadfinished = function() {
    $scope.update_static_files();
  }

  $scope.delete = function(url) {
    $http.delete(url).success(function(response) {
       $scope.update_static_files();
    });
  }

  $scope.update_static_files();

}]);

GLClient.controller('AdminMailCtrl', ['$scope', '$http', function($scope, $http){
  $scope.tabs = [
    {
      title:"Main Configuration",
      template:"views/admin/mail/tab1.html",
      ctrl: TabCtrl
    },
    {
      title:"Notification Templates",
      template:"views/admin/mail/tab2.html",
      ctrl: TabCtrl
    }
  ];
}]);

GLClient.controller('AdminAdvancedCtrl', ['$scope', '$http', function($scope, $http){
  $scope.tabs = [
    {
      title:"Main Configuration",
      template:"views/admin/advanced/tab1.html",
      ctrl: TabCtrl
    },
    {
      title:"Tor2web Settings",
      template:"views/admin/advanced/tab2.html",
      ctrl: TabCtrl
    }
  ];
}]);
