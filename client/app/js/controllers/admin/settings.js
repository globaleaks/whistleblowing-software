GL.controller("AdminSettingsCtrl", ["$scope", "$filter", "$http", "Files", "AdminL10NResource", "DefaultL10NResource",
  function($scope, $filter, $http, Files, AdminL10NResource, DefaultL10NResource){
  $scope.tabs = [
    {
      title: "Settings",
      template: "views/admin/settings/tab1.html"
    }
  ];

  if ($scope.Authentication.session.role === "admin") {
    $scope.tabs = $scope.tabs.concat([
      {
        title: "Files",
        template: "views/admin/settings/tab2.html"
      },
      {
        title: "Languages",
        template: "views/admin/settings/tab3.html"
      },
      {
        title: "Text customization",
        template: "views/admin/settings/tab4.html"
      },
      {
        title: "Advanced",
        template: "views/admin/settings/tab5.html"
      }
    ]);
  }

  $scope.admin_files = [
      {
        "title": "Favicon",
        "varname": "favicon",
        "filename": "custom_favicon.ico",
        "size": "200000"
      },
      {
        "title": "CSS",
        "varname": "css",
        "filename": "custom_stylesheet.css",
        "size": "10000000"
      },
      {
        "title": "JavaScript",
        "varname": "script",
        "filename": "custom_script.js",
        "size": "10000000"
      }
  ];

  if ($scope.Authentication.session.role === "admin") {
    $scope.toggleLangSelect = function() {
      $scope.showLangSelect = true;
    };

    $scope.langNotEnabledFilter = function(lang_obj) {
      return $scope.resources.node.languages_enabled.indexOf(lang_obj.code) === -1;
    };

    $scope.enableLanguage = function(lang_obj) {
      $scope.resources.node.languages_enabled.push(lang_obj.code);
    };

    $scope.removeLang = function(idx, lang_code) {
      if (lang_code === $scope.resources.node.default_language) { return; }
      $scope.resources.node.languages_enabled.splice(idx, 1);
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

    $scope.vars = {
      "language_to_customize": $scope.public.node.default_language
    };
    
    $scope.get_l10n($scope.vars.language_to_customize);
  }

  $scope.files = [];

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

  $scope.resetSubmissions = function() {
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.runAdminOperation("reset_submissions");
    });
  };

  $scope.enableEncryption = function() {
    // do not toggle till confirmation;
    $scope.resources.node.encryption = false;

    if (!$scope.resources.node.encryption) {
      $scope.Utils.openConfirmableModalDialog("views/modals/enable_encryption.html").then(
        function() {
          return $scope.Utils.runAdminOperation("enable_encryption").then(
            function() {
              $scope.Authentication.logout();
            },
            function() {}
          );
        },
        function() { }
      );
    }
  };

  $scope.toggleEscrow = function() {
    // do not toggle till confirmation;
    $scope.resources.node.escrow = !$scope.resources.node.escrow;
    $scope.Utils.runAdminOperation("toggle_escrow", {}, true).then(
      function() {
        $scope.resources.preferences.escrow = !$scope.resources.preferences.escrow;
      },
      function() {}
    );
  };

  $scope.togglePermissionUploadFiles = function() {
    $scope.Authentication.session.permissions.can_upload_files = !$scope.Authentication.session.permissions.can_upload_files;

    if (!$scope.Authentication.session.permissions.can_upload_files) {
      $scope.Utils.runAdminOperation("enable_user_permission_file_upload", {}).then(
        function() {
          $scope.Authentication.session.permissions.can_upload_files = true;
        },
        function() { $scope.Authentication.session.permissions.can_upload_files = false;}
      );
    } else {
      $scope.Utils.runAdminOperation("disable_user_permission_file_upload", {}).then(
        function() {
          $scope.Authentication.session.permissions.can_upload_files = false;
        },
        function() {}
      );
    }
  };

  $scope.update_files();
}]);
