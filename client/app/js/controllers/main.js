GLClient.controller('MainCtrl', ['$q', '$scope', '$rootScope', '$http', '$route', '$routeParams', '$location',  '$filter', '$translate', '$uibModal', '$timeout', 'Authentication', 'Node', 'Contexts', 'Receivers', 'WhistleblowerTip', 'GLCache',
  function($q, $scope, $rootScope, $http, $route, $routeParams, $location, $filter, $translate, $uibModal, $timeout, Authentication, Node, Contexts, Receivers, WhistleblowerTip, GLCache) {
    $rootScope.started = false;
    $rootScope.showLoadingPanel = false;
    $rootScope.successes = [];
    $rootScope.errors = [];

    $scope.rtl = false;
    $scope.app_logo = 'static/logo.png';
    $scope.app_stylesheet = 'css/styles.css';

    $rootScope.language = $location.search().lang;

    $rootScope.embedded = $location.search().embedded === 'true' ? true : false;

    $rootScope.get_auth_headers = Authentication.get_auth_headers;

    $scope.iframeCheck = function() {
      try {
        return window.self !== window.top;
      } catch (e) {
        return true;
      }
    };

    $scope.requireLegacyUploadSupport = function() {
      // Implement the same check implemented but not exported by flowjs
      // https://github.com/flowjs/flow.js/blob/master/src/flow.js#L42
      var support = (
          typeof File !== 'undefined' &&
          typeof Blob !== 'undefined' &&
          typeof FileList !== 'undefined' &&
          (
            !!Blob.prototype.slice || !!Blob.prototype.webkitSlice || !!Blob.prototype.mozSlice ||
            false
          ) // slicing files support
      );

      return !support;
    };

    $scope.browserNotCompatible = function() {
      document.getElementById("BrowserSupported").style.display = "none";
      document.getElementById("BrowserNotSupported").style.display = "block";
    };

    $scope.today = function() {
      return new Date();
    };

    $scope.update = function (model, cb, errcb) {
      var success = {};
      model.$update(function(result) {
        $rootScope.successes.push(success);
      }).then(
        function() { if (cb !== undefined){ cb(); } },
        function() { if (errcb !== undefined){ errcb(); } }
      );
    };

    $scope.go = function (hash) {
      $location.path(hash);
    };

    $scope.randomFluff = function () {
      return Math.random() * 1000000 + 1000000;
    };

    $scope.isWizard = function () {
      var path = $location.path();
      return path === '/wizard';
    };

    $scope.isHomepage = function () {
      var path = $location.path();
      return path === '/';
    };

    $scope.isLoginPage = function () {
      var path = $location.path();
      return (path === '/login' ||
              path === '/admin' ||
              path === '/receipt');
    };

    $scope.isAWhistleblowerPage = function() {
      var path = $location.path();
      return (path === '/' ||
              path === '/start' ||
              path === '/submission' ||
              path === '/receipt' ||
              path === '/status');
    };

    $scope.showLoginForm = function () {
      return (!$scope.isHomepage() &&
              !$scope.isLoginPage());
    };

    $scope.showPrivacyBadge = function() {
      return (!$rootScope.embedded &&
              !$rootScope.node.disable_privacy_badge &&
              $scope.isAWhistleblowerPage());
    };

    $scope.hasSubtitle = function () {
      return $scope.header_subtitle !== '';
    };

    $scope.open_intro = function () {
      if ($scope.intro_opened) {
        return;
      } else {
        $scope.intro_opened = true;
      }

      var modalInstance = $uibModal.open({
        templateUrl: 'views/partials/intro.html',
        controller: 'IntroCtrl',
        size: 'lg',
        scope: $scope
      });

    };

    $scope.set_title = function () {
      if ($rootScope.node) {
        var path = $location.path();
        var statuspage = '/status';
        if (path === '/') {
          $scope.ht = $rootScope.node.header_title_homepage;
        } else if (path === '/submission') {
          $scope.ht = $rootScope.node.header_title_submissionpage;
        } else if (path === '/receipt') {
          if (Authentication.keycode) {
            $scope.ht = $rootScope.node.header_title_receiptpage;
          } else {
            $scope.ht = $filter('translate')("Login");
          }
        } else if (path.substr(0, statuspage.length) === statuspage) {
          $scope.ht = $rootScope.node.header_title_tippage;
        } else {
          $scope.ht = $filter('translate')($scope.header_title);
        }
      }
    };

    $scope.route_check = function () {
      if ($rootScope.node) {
        if ($rootScope.node.wizard_done === false) {
          $location.path('/wizard');
        }

        if (($location.path() === '/') && ($rootScope.node.landing_page === 'submissionpage')) {
          $location.path('/submission');
        }

        if ($location.path() === '/submission' &&
            $scope.anonymous === false &&
            $rootScope.node.tor2web_whistleblower === false) {
          $location.path("/");
        }

        /* Feature implemented for amnesty and currently disabled */
        //$scope.open_intro();
      }
    };

    $scope.show_file_preview = function(content_type) {
      var content_types = [
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/bmp'
      ];

      return content_types.indexOf(content_type) > -1;
    };

    $scope.getXOrderProperty = function(elem) {
      return 'x';
    };

    $scope.getYOrderProperty = function(elem) {
      var key = 'presentation_order';
      if (elem[key] === undefined) {
        key = 'y';
      }
      return key;
    };

    $scope.moveUp = function(elem) {
      var key = $scope.getYOrderProperty(elem);
      elem[key] -= 1;
    };

    $scope.moveDown = function(elem) {
      var key = $scope.getYOrderProperty(elem);
      elem[key] += 1;
    };

    $scope.moveLeft = function(elem) {
      var key = $scope.getXOrderProperty(elem);
      elem[key] -= 1;
    };

    $scope.moveRight = function(elem) {
      var key = $scope.getXOrderProperty(elem);
      elem[key] += 1;
    };

    $scope.deleteFromList = function(list, elem) {
      var idx = list.indexOf(elem);
      if (idx !== -1) {
        list.splice(idx, 1);
      }
    };

    $scope.assignUniqueOrderIndex = function(elements) {
      if (elements.length <= 0) {
        return;
      }

      var key = $scope.getYOrderProperty(elements[0]);
      if (elements.length) {
        var i = 0;
        elements = $filter('orderBy')(elements, key);
        angular.forEach(elements, function (element) {
          element[key] = i;
          i += 1;
        });
      }
    };

    $scope.closeAlert = function(list, index) {
      list.splice(index, 1);
    };

    $rootScope.getUploadUrl = function(url) {
      if ($scope.requireLegacyUploadSupport()) {
        url += '?session=' + $scope.session;
      }

      return url;
    };

    $rootScope.getUploadUrl_lang = function(lang) {
      return function() {
        return $scope.getUploadUrl('admin/l10n/' + lang + '.json');
      };
    };

    $scope.init = function () {
      var deferred = $q.defer();

      $scope.app_logo = 'static/logo.png?' + $scope.randomFluff();
      $scope.app_stylesheet = "css/styles.css?" + $scope.randomFluff();

      Node.get(function(node, getResponseHeaders) {
        $rootScope.node = node;
        // Tor detection and enforcing of usage of HS if users are using Tor
        if (window.location.hostname.match(/^[a-z0-9]{16}\.onion$/)) {
          // A better check on this situation would be
          // to fetch https://check.torproject.org/api/ip
          $rootScope.anonymous = true;
        } else {
          if (window.location.protocol === 'https:') {
             var headers = getResponseHeaders();
             if (headers['x-check-tor'] !== undefined && headers['x-check-tor'] === 'true') {
               $rootScope.anonymous = true;
               if ($rootScope.node.hidden_service && !$scope.iframeCheck()) {
                 // the check on the iframe is in order to avoid redirects
                 // when the application is included inside iframes in order to not
                 // mix HTTPS resources with HTTP resources.
                 window.location.href = $rootScope.node.hidden_service + '/#' + $location.url();
               }
             } else {
               $rootScope.anonymous = false;
             }
          } else {
            $rootScope.anonymous = false;
          }
        }

        $scope.route_check();

        $scope.languages_supported = {};
        $scope.languages_enabled = {};
        $scope.languages_enabled_selector = [];
        angular.forEach(node.languages_supported, function (lang) {
          var code = lang.code;
          var name = lang.name;
          $scope.languages_supported[code] = name;
          if (node.languages_enabled.indexOf(code) !== -1) {
            $scope.languages_enabled[code] = name;
            $scope.languages_enabled_selector.push({"name": name, "code": code});
          }
        });

        $scope.languages_enabled_length = Object.keys(node.languages_enabled).length;

        $scope.show_language_selector = ($scope.languages_enabled_length > 1);

        $scope.set_title();

        var set_language = function(language) {
          if (language === undefined || $rootScope.node.languages_enabled.indexOf(language) === -1) {
            language = node.default_language;
            $rootScope.default_language = node.default_language;
          }

          $rootScope.language = language;

          if (["ar", "he", "ur"].indexOf(language) !== -1) {
            $scope.rtl = true;
            document.getElementsByTagName("html")[0].setAttribute('dir', 'rtl');
          } else {
            $scope.rtl = false;
            document.getElementsByTagName("html")[0].setAttribute('dir', 'ltr');
          }

          $translate.use($rootScope.language);
        };

        set_language($rootScope.language);

        var q1 = Contexts.query(function (contexts) {
          $rootScope.contexts = contexts;
        });

        var q2 = Receivers.query(function (receivers) {
          $rootScope.receivers = receivers;
        });

        $q.all([q1.$promise, q2.$promise]).then(function() {
          $scope.started = true;
          deferred.resolve();
        });

      });

      return deferred.promise;
    };

    $scope.view_tip = function(keycode) {
      keycode = keycode.replace(/\D/g,'');
      new WhistleblowerTip(keycode, function() {
        $location.path('/status');
      });
    };

    $scope.orderByY = function(row) {
      return row[0].y;
    };

    $scope.remove = function(array, index){
      array.splice(index, 1);
    };

    $scope.exportJSON = function(data, filename) {
      var json = angular.toJson(data, 2);
      var blob = new Blob([json], {type: "application/json"});
      filename = filename === undefined ? 'data.json' : filename;
      saveAs(blob, filename);
    };

    $scope.reload = function(new_path) {
      $rootScope.started = false;
      $rootScope.successes = [];
      $rootScope.errors = [];
      GLCache.removeAll();
      $scope.init().then(function() {
        $route.reload();

        if (new_path) {
          $location.path(new_path).replace();
        }
      });
    };

    $scope.uploadedFiles = function(uploads) {
      var sum = 0;

      angular.forEach(uploads, function(flow, key) {
        if (flow !== undefined) {
          sum += flow.files.length;
        }
      });

      return sum;
    };

    $scope.getUploadStatus = function(uploads) {
      var error = false;

      for (var key in uploads) {
        if (uploads.hasOwnProperty(key)) {
          if(uploads[key].isUploading()) {
            return 'uploading';
          }

          for (var i=0; i<uploads[key].files.length; i++) {
            if (uploads[key].files[i].error) {
              error = true;
              break;
            }
          }
        }
      }

      if (error) {
        return 'error';
      } else {
        return 'finished';
      }
    };

    $scope.isUploading = function(uploads) {
      return $scope.getUploadStatus(uploads) === 'uploading';
    };

    $scope.remainingUploadTime = function(uploads) {
      var sum = 0;

      angular.forEach(uploads, function(flow, key) {
        var x = flow.timeRemaining();
        if (x === 'Infinity') {
          return 'Infinity';
        }
        sum += x;
      });

      return sum;
    };

    $scope.uploadProgress = function(uploads) {
      var sum = 0;
      var n = 0;

      angular.forEach(uploads, function(flow, key) {
        sum += flow.progress();
        n += 1;
      });

      if (n === 0 || sum === 0) {
        return 1;
      }

      return sum / n;
    };

  //////////////////////////////////////////////////////////////////

    $scope.$on("$routeChangeStart", function(event, next, current) {
      $scope.route_check();

      var path = $location.path();
      var embedded = '/embedded/';

      if ($location.path().substr(0, embedded.length) === embedded) {
        $rootScope.embedded = true;
        var search = $location.search();
        if (Object.keys(search).length === 0) {
          $location.path(path.replace("/embedded/", "/"));
          $location.search("embedded=true");
        } else {
          $location.url($location.url().replace("/embedded/", "/") + "&embedded=true");
        }
      }
    });

    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
      if (current.$$route) {
        $rootScope.successes = [];
        $rootScope.errors = [];
        $scope.header_title = current.$$route.header_title;
        $scope.header_subtitle = current.$$route.header_subtitle;
        $scope.set_title();
      }
    });

    $scope.$on("REFRESH", function() {
      $scope.reload();
    });

    $scope.$watch(function (scope) {
      return Authentication.session;
    }, function (newVal, oldVal) {
      $scope.session = Authentication.session;
    });

    $rootScope.$watch('language', function (newVal, oldVal) {
      if (newVal && newVal !== oldVal && oldVal !== undefined) {
        $rootScope.$broadcast("REFRESH");
      }
    });

    $rootScope.keypress = function(e) {
       if (((e.which || e.keyCode) === 116) || /* F5 */
           ((e.which || e.keyCode) === 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */
         e.preventDefault();
         $rootScope.$broadcast("REFRESH");
       }
    };

    $scope.init();
  }

]);

GLClient.controller('ModalCtrl', ['$scope', 
  function($scope, $uibModalInstance, error) {
    $scope.error = error;
    $scope.seconds = error.arguments[0];
}]);

TabCtrl = ['$scope', function($scope) {
  /* Empty controller function used to implement TAB pages */
}];

GLClient.controller('DisableEncryptionCtrl', ['$scope', '$uibModalInstance', function($scope, $uibModalInstance){
    $scope.close = function() {
      $uibModalInstance.close(false);
    };

    $scope.no = function() {
      $uibModalInstance.close(false);
    };
    $scope.ok = function() {
      $uibModalInstance.close(true);
    };

}]);

GLClient.controller('IntroCtrl', ['$scope', '$rootScope', '$uibModalInstance', function ($scope, $rootScope, $uibModalInstance) {
  var steps = 3;

  var first_step = 0;

  if ($scope.languages_enabled_length <= 1) {
     first_step = 1;
  }

  $scope.step = first_step;

  $scope.proceed = function () {
    if ($scope.step < steps) {
      $scope.step += 1;
    }
  };

  $scope.back = function () {
    if ($scope.step > first_step) {
      $scope.step -= 1;
    }
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.data = {
    'language': $scope.language
  };

  $scope.$watch("data.language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.data.language;
    }
  });

}]);

GLClient.controller('ConfirmableDialogCtrl', ['$scope', '$uibModalInstance', 'object', function($scope, $uibModalInstance, object) {
  $scope.object = object;

  $scope.ok = function () {
    $uibModalInstance.close($scope.object);
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss('cancel');
  };
}]);
