
GLClient.controller('AdminCtrl',
    ['$scope', '$rootScope', '$http', '$route', '$location', 'Admin', 'Node', 'CONSTANTS',
function($scope, $rootScope, $http, $route, $location, Admin, Node, CONSTANTS) {

  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.https_regexp = CONSTANTS.https_regexp;
  $scope.http_or_https_regexp = CONSTANTS.http_or_https_regexp;
  $scope.timezones = CONSTANTS.timezones;

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
  $scope.languages_enabled_selector = {};

  function CollapseLanguages($scope) {
    $scope.isCollapsed = false;
  }

  Node.get(function(node) {

    $scope.languages_supported = {};
    $scope.languages_enabled = [];
    $scope.languages_enabled_selector = [];
    $.each(node.languages_supported, function(idx) {
      var code = node.languages_supported[idx]['code'];
      $scope.languages_supported[code] = node.languages_supported[idx]['name'];
      if ($.inArray(code, node.languages_enabled) != -1) {
        $scope.languages_enabled[code] = node.languages_supported[idx]['name'];
        $scope.languages_enabled_selector.push({"name": node.languages_supported[idx]['name'],"code": code});
      }
    });

  });


  $scope.$watch('languages_enabled', function(){
    if ($scope.languages_enabled) {
      $scope.languages_enabled_selector = {};
      $.each($scope.languages_supported, function(lang){
        $scope.languages_enabled_edit[lang] = lang in $scope.languages_enabled;
      });
    }

  }, true);

  $scope.$watch('languages_enabled_edit', function() {
    if ($scope.languages_enabled) {
      var languages_enabled_selector = [];
      var change_default = false;
      var language_selected = $scope.admin.node.default_language;
      if (! $scope.languages_enabled_edit[$scope.admin.node.default_language]) {
        change_default = true;
      }

      $.each($scope.languages_supported, function(lang) {
        if ($scope.languages_enabled_edit[lang]) {
          languages_enabled_selector.push({'name': $scope.languages_supported[lang], 'code': lang});

          if (change_default === true) {
            language_selected = lang;
            change_default = false;
          }
        }
      });

      var languages_enabled = [];
      $.each($scope.languages_enabled_edit, function(lang, enabled) {
        if (enabled) {
          languages_enabled.push(lang);
        }
      });

      $scope.admin.node.default_language = language_selected;
      $scope.admin.node.languages_enabled = languages_enabled;

      $scope.languages_enabled_selector = languages_enabled_selector;

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

    $scope.update(node);

    $rootScope.$broadcast("REFRESH");

    $route.reload();
  }

}]);

GLClient.controller('AdminPasswordCtrl', ['$scope', 'changePasswordWatcher',
                    function($scope, changePasswordWatcher) {
    changePasswordWatcher($scope, "admin.node.old_password",
        "admin.node.password", "admin.node.check_password");
}]);

GLClient.controller('AdminFileUploadCtrl', ['$scope', '$http', function($scope, $http){

    $scope.random = Math.round(Math.random()*1000000);

    $scope.uploadfile = false;

    $scope.fileSelected = false;
    $scope.markFileSelected = function () {
      $scope.fileSelected = true;
    };

    $scope.openUploader = function () {
      $scope.uploadfile = true;
    };

    $scope.closeUploader = function () {
      $scope.uploadfile = $scope.fileSelected = false;
    };

    $scope.receiverImgUrl = function () {
      return "/admin/staticfiles/" + $scope.receiver.id;
    };

    $scope.receiverImgReloadUrl = function() {
      return "/static/" + $scope.receiver.id + ".png?" + $scope.random;
    }

}]);

GLClient.controller('AdminContentCtrl', ['$scope', '$http', 'StaticFiles', 'DefaultAppdata',
  function($scope, $http, StaticFiles, DefaultAppdata){
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

  $scope.install_default_fields = function () {

    DefaultAppdata.get(function (res) {

      $http.post('/admin/appdata', res).success(function (response) {

      });

    });
  };

  $scope.update_static_files = function () {
    var updated_staticfiles = StaticFiles.query(function () {
      $scope.staticfiles = updated_staticfiles;
    });
  };

  $scope.uploadfinished = function () {
    $scope.update_static_files();
  };

  $scope.perform_delete = function (url) {
    $http['delete'](url).success(function (response) {
      $scope.update_static_files();
    });
  };

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
      title:"Plaintext Notification Templates",
      template:"views/admin/mail/tab2.html",
      ctrl: TabCtrl
    },
    {
      title:"Encrypted Notification Templates",
      template:"views/admin/mail/tab3.html",
      ctrl: TabCtrl
    }
  ];
}]);

GLClient.controller('AdminAdvancedCtrl', ['$scope', '$http', '$modal', 
                    function($scope, $http, $modal){
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
  $scope.open_modal_allow_unencrypted = function() {
    if ($scope.admin.node.allow_unencrypted)
      return;
    var modalInstance = $modal.open({
      templateUrl: 'views/partials/disable_encryption.html',
      controller: 'DisableEncryptionCtrl',
    });

    modalInstance.result.then(function(result){
      $scope.admin.node.allow_unencrypted = result;
    });
  };

}]);

ConfirmableDialogCtrl = ['$scope', '$modalInstance', 'object', function($scope, $modalInstance, object) {
  $scope.object = object;

  $scope.ok = function () {
    $modalInstance.close($scope.object);
  };

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
}];
