GLClient.
controller('AdminCtrl',
    ['$scope', '$route', '$location', '$filter', 'resources', 'Utils', 'AdminUtils', 'AdminNodeResource', 'UpdateService', 'CONSTANTS',
    function($scope, $route, $location, $filter, resources, Utils, AdminUtils, AdminNodeResource, UpdateService, CONSTANTS) {
  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.hostname_regexp = CONSTANTS.hostname_regexp;
  $scope.onionservice_regexp = CONSTANTS.onionservice_regexp;
  $scope.https_regexp = CONSTANTS.https_regexp;

  // TODO convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.update_service = UpdateService;

  $scope.admin_utils = AdminUtils;

  $scope.admin = resources;

  $scope.updateNode = function() {
    Utils.update($scope.admin.node, function() { $scope.$emit("REFRESH"); });
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
controller('AdminGeneralSettingsCtrl', ['$scope', '$filter', '$http', 'Files', 'AdminL10NResource', 'DefaultL10NResource',
  function($scope, $filter, $http, Files, AdminL10NResource, DefaultL10NResource){
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
        'title': 'CSS',
        'varname': 'css',
        'filename': 'custom_stylesheet.css',
        'type': 'css',
        'size': '1048576'
      },
      {
        'title': 'JavaScript',
        'varname': 'script',
        'filename': 'custom_script.js',
        'type': 'js',
        'size': '1048576'
      }
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

  $scope.files = [];

  $scope.toggleLangSelect = function() {
    $scope.showLangSelect = true;
  };

  $scope.langNotEnabledFilter = function(lang_obj) {
    return $scope.admin.node.languages_enabled.indexOf(lang_obj.code) == -1;
  };

  $scope.enableLanguage = function(lang_obj) {
    $scope.admin.node.languages_enabled.push(lang_obj.code)
  };

  $scope.removeLang = function(idx, lang_code) {
    if (lang_code === $scope.admin.node.default_language) { return; }
    $scope.admin.node.languages_enabled.splice(idx, 1);
  };

  $scope.update_files = function () {
    var updated_files = Files.query(function () {
      $scope.files = updated_files;
    });
  };

  $scope.delete_file = function (url) {
    $http.delete(url).then(function () {
      $scope.update_files();

      $scope.$emit("REFRESH");
    });
  };

  $scope.update_files();
}]).
controller('AdminHomeCtrl', ['$scope', function($scope) {
  $scope.displayNum = 10;
  $scope.showMore = function() {
    $scope.displayNum = undefined;
  }
}]).
controller('AdminAdvancedCtrl', ['$scope', '$uibModal', 'CONSTANTS',
  function($scope, $uibModal, CONSTANTS){
  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/advanced/tab1.html"
    },
    {
      title:"URL shortener",
      template:"views/admin/advanced/tab2.html"
    },
  ];

  if ($scope.admin.node.root_tenant) {
    $scope.tabs.push({
      title:"Anomaly detection thresholds",
      template:"views/admin/advanced/tab3.html"
    });
  }


  $scope.open_modal_allow_unencrypted = function() {
    if (!$scope.admin.node.allow_unencrypted) {
      return;
    }

    var modalInstance = $uibModal.open({
      templateUrl: 'views/partials/disable_encryption.html',
      controller: 'ModalCtrl'
    });

    modalInstance.result.then(function(result){
      $scope.admin.node.allow_unencrypted = result;
    });
  };

  $scope.shortener_shorturl_regexp = CONSTANTS.shortener_shorturl_regexp;
  $scope.shortener_longurl_regexp = CONSTANTS.shortener_longurl_regexp;

  $scope.new_shorturl = {};

  $scope.add_shorturl = function() {
    var shorturl = new $scope.admin_utils.new_shorturl();

    shorturl.shorturl = $scope.new_shorturl.shorturl;
    shorturl.longurl = $scope.new_shorturl.longurl;

    shorturl.$save(function(new_shorturl){
      $scope.admin.shorturls.push(new_shorturl);
      $scope.new_shorturl = {};
    });
  };
}]).
controller('AdminShorturlEditCtrl', ['$scope', 'AdminShorturlResource',
  function($scope, AdminShorturlResource) {
    $scope.delete_shorturl = function(shorturl) {
      AdminShorturlResource.delete({
        id: shorturl.id
      }, function(){
        var idx = $scope.admin.shorturls.indexOf(shorturl);
        $scope.admin.shorturls.splice(idx, 1);
      });
    };
}]).
controller('AdminMailCtrl', ['$scope', '$http', 'Utils', 'AdminNotificationResource',
  function($scope, $http, Utils, AdminNotificationResource){

  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/mail/tab1.html"
    },
    {
      title:"Notification templates",
      template:"views/admin/mail/tab2.html"
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
}]).
controller('AdminReviewModalCtrl', ['$scope', '$uibModalInstance', 'targetFunc',
  function($scope, $uibModalInstance, targetFunc) {
  $scope.cancel = $uibModalInstance.close;

  $scope.ok = function() {
    return targetFunc().then($uibModalInstance.close);
  };
}]);
