GLClient.
controller("AdminCtrl",
    ["$scope", "$route", "$location", "$filter", "resources", "AdminNodeResource", "UpdateService", "CONSTANTS",
    function($scope, $route, $location, $filter, resources, AdminNodeResource, UpdateService, CONSTANTS) {
  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.hostname_regexp = CONSTANTS.hostname_regexp;
  $scope.onionservice_regexp = CONSTANTS.onionservice_regexp;
  $scope.https_regexp = CONSTANTS.https_regexp;

  // TODO convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split("/").slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.update_service = UpdateService;

  $scope.admin = resources;

  $scope.updateNode = function() {
    $scope.Utils.update($scope.admin.node, function() { $scope.$emit("REFRESH"); });
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
controller("AdminGeneralSettingsCtrl", ["$scope", "$filter", "$http", "Files", "AdminL10NResource", "DefaultL10NResource",
  function($scope, $filter, $http, Files, AdminL10NResource, DefaultL10NResource){
  $scope.tabs = [
    {
      title: "Main configuration",
      template: "views/admin/content/tab1.html"
    }
  ];

  if ($scope.session.role === "admin") {
    $scope.tabs = $scope.tabs.concat([
      {
        title: "Theme customization",
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
    ]);
  }

  $scope.admin_files = [
      {
        "title": "CSS",
        "varname": "css",
        "filename": "custom_stylesheet.css",
        "type": "css",
        "size": "1048576"
      },
      {
        "title": "JavaScript",
        "varname": "script",
        "filename": "custom_script.js",
        "type": "js",
        "size": "1048576"
      }
  ];

  $scope.vars = {
    "language_to_customize": $scope.node.default_language
  };

  $scope.get_l10n = function(lang) {
    if (!lang) {
      return;
    }

    $scope.custom_texts = AdminL10NResource.get({"lang": lang});
    DefaultL10NResource.get({"lang": lang}, function(default_texts) {
      var list = [];
      for (var key in default_texts) {
        if (default_texts.hasOwnProperty(key)) {
          var value = default_texts[key];
          if (value.length > 150) {
            value = value.substr(0, 150) + "...";
          }
          list.push({"key": key, "value": value});
        }
      }

      $scope.default_texts = default_texts;
      $scope.custom_texts_selector = $filter("orderBy")(list, "value");
    });
  };

  $scope.get_l10n($scope.vars.language_to_customize);

  $scope.files = [];

  $scope.toggleLangSelect = function() {
    $scope.showLangSelect = true;
  };

  $scope.langNotEnabledFilter = function(lang_obj) {
    return $scope.admin.node.languages_enabled.indexOf(lang_obj.code) === -1;
  };

  $scope.enableLanguage = function(lang_obj) {
    $scope.admin.node.languages_enabled.push(lang_obj.code);
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
controller("AdminHomeCtrl", ["$scope", function($scope) {
  $scope.displayNum = 10;
  $scope.showMore = function() {
    $scope.displayNum = undefined;
  };
}]).
controller("AdminAdvancedCtrl", ["$scope", "$uibModal", "CONSTANTS",
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

    /*
    $scope.tabs.push({
      title: "Backups",
      template: "views/admin/advanced/tab4.html"
    });
    */
  }

  $scope.shortener_shorturl_regexp = CONSTANTS.shortener_shorturl_regexp;
  $scope.shortener_longurl_regexp = CONSTANTS.shortener_longurl_regexp;

  $scope.new_shorturl = {};

  $scope.add_shorturl = function() {
    var shorturl = new $scope.AdminUtils.new_shorturl();

    shorturl.shorturl = $scope.new_shorturl.shorturl;
    shorturl.longurl = $scope.new_shorturl.longurl;

    shorturl.$save(function(new_shorturl){
      $scope.admin.shorturls.push(new_shorturl);
      $scope.new_shorturl = {};
    });
  };
}]).
controller("AdminShorturlEditCtrl", ["$scope", "AdminShorturlResource",
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
controller("AdminMailCtrl", ["$scope", "$http", "AdminNotificationResource",
  function($scope, $http, AdminNotificationResource) {

  $scope.text_templates = [
    "activation_mail_template",
    "activation_mail_title",
    "admin_anomaly_activities",
    "admin_anomaly_disk_high",
    "admin_anomaly_disk_low",
    "admin_anomaly_mail_template",
    "admin_anomaly_mail_title",
    "admin_pgp_alert_mail_template",
    "admin_pgp_alert_mail_title",
    "admin_signup_alert_mail_template",
    "admin_signup_alert_mail_title",
    "admin_test_mail_template",
    "admin_test_mail_title",
    "comment_mail_template",
    "comment_mail_title",
    "email_validation_mail_template",
    "email_validation_mail_title",
    "export_message_recipient",
    "export_message_whistleblower",
    "export_template",
    "file_mail_template",
    "file_mail_title",
    "https_certificate_expiration_mail_template",
    "https_certificate_expiration_mail_title",
    "https_certificate_renewal_failure_mail_template",
    "https_certificate_renewal_failure_mail_title",
    "identity_access_authorized_mail_template",
    "identity_access_authorized_mail_title",
    "identity_access_denied_mail_template",
    "identity_access_denied_mail_title",
    "identity_access_request_mail_template",
    "identity_access_request_mail_title",
    "identity_provided_mail_template",
    "identity_provided_mail_title",
    "message_mail_template",
    "message_mail_title",
    "password_reset_complete_mail_template",
    "password_reset_complete_mail_title",
    "password_reset_validation_mail_template",
    "password_reset_validation_mail_title",
    "pgp_alert_mail_template",
    "pgp_alert_mail_title",
    "receiver_notification_limit_reached_mail_template",
    "receiver_notification_limit_reached_mail_title",
    "signup_mail_template",
    "signup_mail_title",
    "software_update_available_mail_template",
    "software_update_available_mail_title",
    "tip_expiration_summary_mail_template",
    "tip_expiration_summary_mail_title",
    "tip_mail_template",
    "tip_mail_title",
    "user_credentials",
    "2fa_mail_template",
    "2fa_mail_title",
  ];

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
    return $http({
      method: "POST",
      url: "/admin/notification/mail",
    });
  };

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.admin.notification)
    .$promise.then(function() { return sendTestMail(); }, function() { });
  };
}]).
controller("AdminReviewModalCtrl", ["$scope", "$uibModalInstance", "targetFunc",
  function($scope, $uibModalInstance, targetFunc) {
  $scope.cancel = $uibModalInstance.close;

  $scope.ok = function() {
    return targetFunc().then($uibModalInstance.close);
  };
}]);
