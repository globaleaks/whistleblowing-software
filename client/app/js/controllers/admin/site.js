GL.
controller("AdminGeneralSettingsCtrl", ["$scope", "$filter", "$http", "Files", "AdminL10NResource", "DefaultL10NResource",
  function($scope, $filter, $http, Files, AdminL10NResource, DefaultL10NResource){
  $scope.tabs = [
    {
      title: "Main configuration",
      template: "views/admin/content/tab1.html"
    }
  ];

  if ($scope.Authentication.session.role === "admin") {
    $scope.tabs = $scope.tabs.concat([
      {
        title: "Theme customization",
        template: "views/admin/content/tab2.html"
      },
      {
        title: "Files",
        template: "views/admin/content/tab3.html"
      },
      {
        title: "Languages",
        template: "views/admin/content/tab4.html"
      },
      {
        title: "Text customization",
        template: "views/admin/content/tab5.html"
      }
    ]);
  }

  $scope.admin_files = [
      {
        "title": "Favicon",
        "varname": "favicon",
        "filename": "custom_favicon.ico",
        "type": "ico",
        "size": "131072"
      },
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
    "language_to_customize": $scope.public.node.default_language
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
    return $scope.resources.node.languages_enabled.indexOf(lang_obj.code) === -1;
  };

  $scope.enableLanguage = function(lang_obj) {
    $scope.resources.node.languages_enabled.push(lang_obj.code);
  };

  $scope.removeLang = function(idx, lang_code) {
    if (lang_code === $scope.resources.node.default_language) { return; }
    $scope.resources.node.languages_enabled.splice(idx, 1);
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
}]);
