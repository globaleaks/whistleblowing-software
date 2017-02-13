GLClient.controller('AdminCtrl',
    ['$scope', '$route', '$location', '$filter', 'Admin', 'AdminUtils', 'CONSTANTS',
    function($scope, $route, $location, $filter, Admin, AdminUtils, CONSTANTS) {
  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.https_regexp = CONSTANTS.https_regexp;
  $scope.tor_regexp = CONSTANTS.tor_regexp;

  // XXX convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.admin_utils = AdminUtils;

  $scope.admin = new Admin(function() {
    $scope.languages_enabled_edit = {};
    $scope.languages_enabled_selector = [];

    $scope.languages_supported = {};
    $scope.languages_enabled = [];
    $scope.languages_enabled_selector = [];
    angular.forEach($scope.admin.node.languages_supported, function(lang) {
      var code = lang.code;
      var name = lang.name;
      $scope.languages_supported[code] = name;
      if ($scope.admin.node.languages_enabled.indexOf(code) !== -1) {
        $scope.languages_enabled[code] = name;
        $scope.languages_enabled_selector.push({"name": name,"code": code});
      }
    });

    $scope.languages_enabled_selector = $filter('orderBy')($scope.languages_enabled_selector, 'code');

    $scope.$watch('languages_enabled', function() {
      if ($scope.languages_enabled) {
        $scope.languages_enabled_edit = {};
        angular.forEach($scope.languages_supported, function(lang, code){
          $scope.languages_enabled_edit[code] = code in $scope.languages_enabled;
        });
      }
    }, true);

    $scope.$watch('languages_enabled_edit', function() {
      if ($scope.languages_enabled) {
        var languages_enabled_selector = [];
        var change_default = false;
        var language_selected = $scope.admin.node.default_language;
        if (!$scope.languages_enabled_edit[$scope.admin.node.default_language]) {
          change_default = true;
        }

        angular.forEach($scope.languages_supported, function(lang, code) {
          if ($scope.languages_enabled_edit[code]) {
            languages_enabled_selector.push({'name': lang, 'code': code});

            if (change_default === true) {
              language_selected = code;
              change_default = false;
            }
          }
        });

        var languages_enabled = [];
        angular.forEach($scope.languages_enabled_edit, function(enabled, code) {
          if (enabled) {
            languages_enabled.push(code);
          }
        });

        $scope.admin.node.default_language = language_selected;
        $scope.admin.node.languages_enabled = languages_enabled;

        $scope.languages_enabled_selector = languages_enabled_selector;

      }
    }, true);
  });

  // We need to have a special function for updating the node since we need to add old_password and password attribute
  // if they are not present
  $scope.updateNode = function(node) {
    if (node.password === undefined) {
      node.password = "";
    }

    if (node.check_password === undefined) {
      node.password = "";
    }

    if (node.old_password === undefined) {
      node.old_password = "";
    }

    var cb = function() {
      $scope.$emit("REFRESH");
    };

    $scope.Utils.update(node, cb);
  };

  $scope.newItemOrder = function(objects, key) {
    if (objects.length === 0) {
      return 0;
    }

    var max = 0;
    angular.forEach(objects, function(object) {
      if (object[key] > max) {
        max = object[key];
      }
    });

    return max + 1;
  };
}]).
controller('AdminGeneralSettingsCtrl', ['$scope', '$filter', '$http', 'StaticFiles', 'AdminL10NResource', 'DefaultL10NResource',
  function($scope, $filter, $http, StaticFiles, AdminL10NResource, DefaultL10NResource){
  $scope.tabs = [
    {
      title:"Main configuration",
      template: "views/admin/content/tab1.html"
    },
    {
      title:"Theme customization",
      template: "views/admin/content/tab2.html"
    },
    {
      title: "Languages",
      template: "views/admin/content/tab3.html"
    },
    {
      title: "Text customization",
      template: "views/admin/content/tab4.html"
    }
  ];

  $scope.admin_files = [
      {
        'title': 'Custom CSS',
        'varname': 'css',
        'filename': 'custom_stylesheet.css',
        'type': 'css',
        'size': '1048576'
      },
      {
        'title': 'Custom JavaScript',
        'varname': 'script',
        'filename': 'custom_script.js',
        'type': 'js',
        'size': '1048576'
      },
      {
        'title': 'Custom homepage',
        'varname': 'homepage',
        'filename': 'custom_homepage.html',
        'type': 'html',
        'size': '1048576'
      },
  ];

  $scope.vars = {
    'language_to_customize': $scope.node.default_language
  };

  $scope.get_l10n = function(lang) {
    if (!lang) {
      return;
    }

    $scope.custom_texts = AdminL10NResource.get({'lang': lang});
    DefaultL10NResource.get({'lang': lang}, function(default_texts) {
      var list = [];
      for (var key in default_texts) {
        if (default_texts.hasOwnProperty(key)) {
          var value = default_texts[key];
          if (value.length > 150) {
            value = value.substr(0, 150) + "...";
          }
          list.push({'key': key, 'value': value});
        }
      }

      $scope.default_texts = default_texts;
      $scope.custom_texts_selector = $filter('orderBy')(list, 'value');
    });
  };

  $scope.get_l10n($scope.vars.language_to_customize);

  $scope.staticfiles = [];

  $scope.update_static_files = function () {
    var updated_staticfiles = StaticFiles.query(function () {
      $scope.staticfiles = updated_staticfiles;
    });
  };

  $scope.delete_resource = function (url, refresh) {
    return $http.delete(url).then(function () {
      if (refresh) {
        $scope.$emit("REFRESH");
      }
    });
  };

  $scope.delete_file = function (url) {
    $http.delete(url).then(function () {
      $scope.update_static_files();
    });
  };

  $scope.update_static_files();
}]).
controller('AdminAdvancedCtrl', ['$scope', '$uibModal',
  function($scope, $uibModal){
  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/advanced/tab1.html"
    },
    {
      title:"HTTPS settings",
      template:"views/admin/advanced/tab2.html"
    },
    {
      title:"Anomaly detection thresholds",
      template:"views/admin/advanced/tab3.html"
    }
  ];

  $scope.open_modal_allow_unencrypted = function() {
    if (!$scope.admin.node.allow_unencrypted) {
      return;
    }

    var modalInstance = $uibModal.open({
      templateUrl: 'views/partials/disable_encryption.html',
      controller: 'DisableEncryptionCtrl'
    });

    modalInstance.result.then(function(result){
      $scope.admin.node.allow_unencrypted = result;
    });
  };
}]).
controller('AdminMailCtrl', ['$scope', '$http', 'Admin', 'AdminNotificationResource',
  function($scope, $http, Admin, AdminNotificationResource){
  $scope.notif = Admin.notification;

  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/mail/tab1.html"
    },
    {
      title:"Admin notification templates",
      template:"views/admin/mail/tab2.html"
    },
    {
      title:"Recipient notification templates",
      template:"views/admin/mail/tab3.html"
    },
    {
      title:"Exception notification",
      template:"views/admin/mail/tab4.html"
    }
  ];

  var sendTestMail = function() {
    $http({
      method: 'POST',
      url: '/admin/notification/mail',
    });
  };

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.admin.notification)
    .$promise.then(function() { sendTestMail(); }, function() { });
  };
}]);
