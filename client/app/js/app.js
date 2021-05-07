/* eslint no-unused-vars: ["error", { "varsIgnorePattern": "^GL|\$locale$" }] */

var _flowFactoryProvider;

var GL = angular.module("GL", [
    "angular.filter",
    "ngAria",
    "ngRoute",
    "ui.bootstrap",
    "ui.select",
    "tmh.dynamicLocale",
    "flow",
    "monospaced.qrcode",
    "pascalprecht.translate",
    "ngCsv",
    "ngResource",
    "ngSanitize",
    "ngFileSaver",
    "ng-showdown"
]).
  config(["$compileProvider", function($compileProvider) {
    $compileProvider.debugInfoEnabled(false);
}]).
  config(["$httpProvider", function($httpProvider) {
    $httpProvider.interceptors.push("globaleaksRequestInterceptor");
}]).
  config(["$locationProvider", function($locationProvider) {
    $locationProvider.hashPrefix("");
}]).
  config(["$showdownProvider", function($showdownProvider) {
    $showdownProvider.setOption("sanitize", true);
    $showdownProvider.setOption("openLinksInNewWindow", true);
}]).
  config(["$provide", function($provide) {
    $provide.decorator("$templateRequest", ["$delegate", function($delegate) {
      // This decorator is required in order to inject the "true" for setting ignoreRequestError
      // in relation to https://docs.angularjs.org/error/$compile/tpload
      var fn = $delegate;

      $delegate = function(tpl) {
        for (var key in fn) {
          $delegate[key] = fn[key];
        }

        return fn.apply(this, [tpl, true]);
      };

      return $delegate;
    }]);

    $provide.decorator("$exceptionHandler", ["$delegate", "$injector", "stacktraceService", function ($delegate, $injector, stacktraceService) {
      var uuid4RE = /([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/g;
      var uuid4Empt = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
      // Note this RE is different from our usual email validator
      var emailRE = /(([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}.[\w]{1,100})/g;
      var emailEmpt = "~~~~~~@~~~~~~";

      function scrub(s) {
        return s.replace(uuid4RE, uuid4Empt).replace(emailRE, emailEmpt);
      }

      return function(exception, cause) {
          var $rootScope = $injector.get("$rootScope");

          if (typeof $rootScope.exceptions_count === "undefined") {
            $rootScope.exceptions_count = 0;
          }

          $rootScope.exceptions_count += 1;

          if ($rootScope.exceptions_count >= 3) {
            // Give each client the ability to forward only the first 3 exceptions
            // scattered; this is also important to avoid looping exceptions to
            // cause looping POST requests.
            return;
          }

          $delegate(exception, cause);

          stacktraceService.fromError(exception).then(function(result) {
              var errorData = angular.toJson({
              errorUrl: $injector.get("$location").path(),
              errorMessage: exception.toString(),
              stackTrace: result,
              agent: navigator.userAgent
            });

            $injector.get("$http").post("api/exception", scrub(errorData));
          });
      };
    }]);
}]).
  config(["$qProvider", function($qProvider) {
    $qProvider.errorOnUnhandledRejections(false);
}]).
  config(["$rootScopeProvider", function($rootScopeProvider) {
    // Raise the default digest loop limit to 30 because of the template recursion used by fields:
    // https://github.com/angular/angular.js/issues/6440
    $rootScopeProvider.digestTtl(30);
}]).
  config(["$routeProvider", function($routeProvider) {
    function requireAuth(role) {
      return ["Access", function(Access) { return Access.isAuthenticated(role); }];
    }

    function noAuth() {
      return ["Access", function(Access) { return Access.isUnauth(); }];
    }

    function allKinds() {
      return ["Access", function(Access) { return Access.OK; }];
    }

    function fetchResources(role, lst) {
      return ["$q", "$rootScope", "Access", "AdminAuditLogResource", "AdminContextResource", "AdminQuestionnaireResource", "AdminStepResource", "AdminFieldResource", "AdminFieldTemplateResource", "AdminUserResource", "AdminNodeResource", "AdminNotificationResource", "AdminRedirectResource", "AdminTenantResource", "FieldAttrs", "TipsCollection", "JobsAuditLog", "AdminSubmissionStatusResource", function($q, $rootScope, Access, AdminAuditLogResource, AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminNodeResource, AdminNotificationResource, AdminRedirectResource, AdminTenantResource, FieldAttrs, TipsCollection, JobsAuditLog, AdminSubmissionStatusResource) {
        var resourcesPromises = {
          auditlog: function() { return AdminAuditLogResource.query().$promise; },
          node: function() { return AdminNodeResource.get().$promise; },
          contexts: function() { return AdminContextResource.query().$promise; },
          field_attrs: function() { return FieldAttrs.get().$promise; },
          fieldtemplates: function() { return AdminFieldTemplateResource.query().$promise; },
          users: function() { return AdminUserResource.query().$promise; },
          notification: function() { return AdminNotificationResource.get().$promise; },
          redirects: function() { return AdminRedirectResource.query().$promise; },
          tenants: function() { return AdminTenantResource.query().$promise; },
          tips: function() { return TipsCollection.query().$promise; },
          jobs: function() { return JobsAuditLog.query().$promise; },
          questionnaires: function() { return AdminQuestionnaireResource.query().$promise; },
          submission_statuses: function() { return AdminSubmissionStatusResource.query().$promise; },
        };

        return Access.isAuthenticated(role).then(function() {
          var promises = {};

          for (var i = 0; i < lst.length; i++) {
             var name = lst[i];
             promises[name] = resourcesPromises[name]();
          }

          return $q.all(promises).then(function(resources) {
            $rootScope.resources = resources;
          });
        });
      }];
    }

    $routeProvider.
      when("/wizard", {
        templateUrl: "views/wizard/main.html",
        controller: "WizardCtrl",
        header_title: "Platform wizard",
        resolve: {
          access: allKinds()
        }
      }).
      when("/submission", {
        templateUrl: "views/whistleblower/submission.html",
        controller: "SubmissionCtrl",
        header_title: "",
        resolve: {
          access: noAuth()
        }
      }).
      when("/activation", {
        templateUrl: "views/signup/activation.html",
        controller: "SignupActivationCtrl",
        header_title: "Create your whistleblowing platform",
        resolve: {
          access: allKinds()
        }
      }).
      when("/status/:tip_id", {
        templateUrl: "views/recipient/tip.html",
        controller: "TipCtrl",
        header_title: "Report",
        resolve: {
          access: requireAuth("receiver")
        }
      }).
      when("/actions/forcedpasswordchange", {
        templateUrl: "views/actions/forced_password_change.html",
        controller: "ForcedPasswordChangeCtrl",
        header_title: "Change your password",
        resolve: {
          access: requireAuth("*")
        }
      }).
      when("/actions/forcedtwofactor", {
        templateUrl: "views/actions/forced_two_factor.html",
        controller: "EnableTwoFactorAuthCtrl",
        header_title: "Enable two factor authentication",
        resolve: {
          access: requireAuth("*")
        }
      }).
      when("/recipient/home", {
        templateUrl: "views/recipient/home.html",
        header_title: "Home",
        sidebar: "views/recipient/sidebar.html",
        resolve: {
          access: requireAuth("receiver")
        }
      }).
      when("/recipient/preferences", {
        templateUrl: "views/partials/preferences.html",
        controller: "PreferencesCtrl",
        header_title: "Preferences",
        sidebar: "views/recipient/sidebar.html",
        resolve: {
          access: requireAuth("receiver")
        }
      }).
      when("/recipient/content", {
        templateUrl: "views/recipient/content.html",
        controller: "AdminCtrl",
        header_title: "Site settings",
        sidebar: "views/recipient/sidebar.html",
        resolve: {
          resources: fetchResources("receiver", ["node"]),
        }
      }).
      when("/recipient/reports", {
        templateUrl: "views/recipient/tips.html",
        controller: "ReceiverTipsCtrl",
        header_title: "Reports",
        resolve: {
          access: requireAuth("receiver")
        }
      }).
      when("/admin/home", {
        templateUrl: "views/admin/home.html",
        controller: "AdminCtrl",
        header_title: "Home",
        sidebar: "views/admin/sidebar.html",
        resolve: {
           access: requireAuth("admin"),
           resources: fetchResources("admin", ["node", "users"])
        }
      }).
      when("/admin/preferences", {
        templateUrl: "views/partials/preferences.html",
        controller: "PreferencesCtrl",
        header_title: "Preferences",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node"])
        }
      }).
      when("/admin/content", {
        templateUrl: "views/admin/content.html",
        controller: "AdminCtrl",
        header_title: "Site settings",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node"])
        }
      }).
      when("/admin/contexts", {
        templateUrl: "views/admin/contexts.html",
        controller: "AdminCtrl",
        header_title: "Contexts",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["contexts", "node", "questionnaires", "users"])
        }
      }).
      when("/admin/questionnaires", {
        templateUrl: "views/admin/questionnaires.html",
        controller: "AdminCtrl",
        header_title: "Questionnaires",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["fieldtemplates", "field_attrs", "node", "questionnaires", "users"])
        }
      }).
      when("/admin/users", {
        templateUrl: "views/admin/users.html",
        controller: "AdminCtrl",
        header_title: "Users",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "users"])
        }
      }).
      when("/admin/notifications", {
        templateUrl: "views/admin/notifications.html",
        controller: "AdminCtrl",
        header_title: "Notification settings",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "notification"])
        }
      }).
      when("/admin/network", {
        templateUrl: "views/admin/network.html",
        controller: "AdminCtrl",
        header_title: "Network settings",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "redirects"])
        }
      }).
      when("/admin/advanced", {
        templateUrl: "views/admin/advanced.html",
        controller: "AdminCtrl",
        header_title: "Advanced settings",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "questionnaires", "users"])
        }
      }).
      when("/admin/auditlog", {
        templateUrl: "views/admin/auditlog.html",
        controller: "AdminCtrl",
        header_title: "Audit log",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["auditlog", "node", "jobs", "tips", "users"])
        }
      }).
      when("/admin/sites", {
        templateUrl: "views/admin/sites.html",
        controller: "AdminCtrl",
        header_title: "Sites management",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "tenants"])
        }
      }).
      when("/admin/casemanagement", {
        templateUrl: "views/admin/casemanagement.html",
        controller: "AdminCtrl",
        header_title: "Case management",
        sidebar: "views/admin/sidebar.html",
        resolve: {
          access: requireAuth("admin"),
          resources: fetchResources("admin", ["node", "submission_statuses"])
        }
      }).
      when("/custodian/home", {
        templateUrl: "views/custodian/home.html",
        header_title: "Home",
        sidebar: "views/custodian/sidebar.html",
        resolve: {
          access: requireAuth("custodian")
        }
      }).
      when("/custodian/preferences", {
        templateUrl: "views/partials/preferences.html",
	controller: "PreferencesCtrl",
        header_title: "Preferences",
        sidebar: "views/custodian/sidebar.html",
        resolve: {
          access: requireAuth("custodian")
        }
      }).
      when("/custodian/content", {
        templateUrl: "views/custodian/content.html",
        controller: "AdminCtrl",
        header_title: "Site settings",
        sidebar: "views/custodian/sidebar.html",
        resolve: {
          access: requireAuth("custodian"),
          resources: fetchResources("custodian", ["node"])
        }
      }).
      when("/custodian/requests", {
        templateUrl: "views/custodian/identity_access_requests.html",
        header_title: "Requests",
        resolve: {
          access: requireAuth("custodian")
        }
      }).
      when("/login", {
        templateUrl: "views/login/main.html",
        controller: "LoginCtrl",
        header_title: "Log in",
        resolve: {
          access: noAuth()
        }
      }).
      when("/admin", {
        templateUrl: "views/login/main.html",
        controller: "LoginCtrl",
        header_title: "Log in",
        resolve: {
          access: noAuth()
        }
      }).
      when("/multisitelogin", {
        templateUrl: "views/login/main.html",
        controller: "LoginCtrl",
        header_title: "Log in",
        resolve: {
          access: noAuth()
        }
      }).
      when("/login/passwordreset", {
        templateUrl: "views/passwordreset/main.html",
        controller: "PasswordResetCtrl",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/login/passwordreset/requested", {
        templateUrl: "views/passwordreset/requested.html",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/login/passwordreset/failure/token", {
        templateUrl: "views/passwordreset/failure_token.html",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/login/passwordreset/failure/recovery", {
        templateUrl: "views/passwordreset/failure_recovery.html",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/password/reset", {
        templateUrl: "views/empty.html",
        controller: "PasswordResetCompleteCtrl",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/password/reset/2fa", {
        templateUrl: "views/passwordreset/2fa.html",
        controller: "PasswordResetCompleteCtrl",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/password/reset/recovery", {
        templateUrl: "views/passwordreset/recovery.html",
        controller: "PasswordResetCompleteCtrl",
        header_title: "Password reset",
        resolve: {
          access: noAuth()
        }
      }).
      when("/email/validation/success", {
        templateUrl: "views/email_validation_success.html",
        controller: "EmailValidationCtrl",
        header_title: "",
        resolve: {
          access: noAuth()
        }
      }).
      when("/email/validation/failure", {
        templateUrl: "views/email_validation_failure.html",
        controller: "EmailValidationCtrl",
        header_title: "",
        resolve: {
          access: noAuth()
        }
      }).
      when("/", {
        templateUrl: "views/home.html",
        header_title: ""
      }).
      otherwise({
        redirectTo: "/"
      });
}]).
  config(["$translateProvider", function($translateProvider) {
    $translateProvider.useStaticFilesLoader({
      prefix: "l10n/",
      suffix: ""
    });

    $translateProvider.useInterpolation("noopInterpolation");
    $translateProvider.useSanitizeValueStrategy("escape");
}]).
  config(["$uibModalProvider", function($uibModalProvider) {
    $uibModalProvider.options.backdrop = "static";
    $uibModalProvider.options.keyboard = false;
    $uibModalProvider.options.focus = true;
}]).
  config(["$uibTooltipProvider", function($uibTooltipProvider) {
    $uibTooltipProvider.options({placement: "auto", appendToBody: true, trigger: "mouseenter"});
}]).
  config(["tmhDynamicLocaleProvider", function(tmhDynamicLocaleProvider) {
    var map = {
      "ca@valencia": "ca-es-valencia",
      "dv": "en",
      "sl-si": "sl"
    };

    tmhDynamicLocaleProvider.addLocalePatternValue("map", map);

    tmhDynamicLocaleProvider.localeLocationPattern("{{map[locale] ? 'lib/js/locale/angular-locale_' + map[locale] +'.js' : 'lib/js/locale/angular-locale_' + locale +'.js'}}");
}]).
  config(["flowFactoryProvider", function (flowFactoryProvider) {
    // Trick to move the flowFactoryProvider config inside run block.
    _flowFactoryProvider = flowFactoryProvider;
}]).
  run(["$rootScope", "$http", "$route", "$routeParams", "$window", "$location",  "$filter", "$translate", "$uibModal", "$templateCache", "Authentication", "PublicResource", "Utils", "AdminUtils", "fieldUtilities", "GLTranslate", "Access",
      function($rootScope, $http, $route, $routeParams, $window, $location, $filter, $translate, $uibModal, $templateCache, Authentication, PublicResource, Utils, AdminUtils, fieldUtilities, GLTranslate, Access) {
    $rootScope.started = false;

    $rootScope.Authentication = Authentication;
    $rootScope.GLTranslate = GLTranslate;
    $rootScope.Utils = Utils;
    $rootScope.fieldUtilities = fieldUtilities;
    $rootScope.AdminUtils = AdminUtils;

    $rootScope.showLoadingPanel = false;
    $rootScope.errors = [];

    _flowFactoryProvider.defaults = {
      chunkSize: 1000 * 1024,
      forceChunkSize: true,
      testChunks: false,
      simultaneousUploads: 1,
      generateUniqueIdentifier: function () {
        return Math.random() * 1000000 + 1000000;
      },
      headers: function() {
        return $rootScope.Authentication.get_headers();
      }
    };

    $rootScope.setPage = function(page) {
      $location.path("/");
      $rootScope.page = page;
      $rootScope.Utils.set_title();
    };

    $rootScope.setHomepage = function() {
      $rootScope.setPage("homepage");
      $rootScope.reload();
    };

    $rootScope.closeAlert = function (list, index) {
      list.splice(index, 1);
    };

    $rootScope.open_confidentiality_modal = function () {
      $uibModal.open({
        controller: "ConfirmableModalCtrl",
        templateUrl: "views/partials/security_awareness_confidentiality.html",
        size: "lg",
        scope: $rootScope
      });
    };

    $rootScope.open_disclaimer_modal = function () {
      $uibModal.open({
        templateUrl: "views/partials/disclaimer.html",
        controller: "ConfirmableModalCtrl",
        size: "lg",
	resolve: {
          arg: null,
          confirmFun: function() { return function() { $rootScope.setPage("submissionpage"); }; },
          cancelFun: null
	}
      });
    };

    $rootScope.evaluateConfidentialityModalOpening = function () {
      if (!$rootScope.connection.tor &&
          !$rootScope.connection.https &&
          !$rootScope.confidentiality_warning_opened &&
          ["localhost", "127.0.0.1"].indexOf($location.host()) === -1) {
        $rootScope.confidentiality_warning_opened = true;
        $rootScope.open_confidentiality_modal();
        return true;
      }

      return false;
    };

    $rootScope.evaluateDisclaimerModalOpening = function () {
      if ($rootScope.public.node.enable_disclaimer &&
          !$rootScope.disclaimer_modal_opened) {
        $rootScope.disclaimer_modal_opened = true;
        $rootScope.open_disclaimer_modal();
        return true;
      }

      return false;
    };

    $rootScope.init = function () {
      return PublicResource.get(function(result, getResponseHeaders) {
        var elem;

        $rootScope.public = result;

        if ($rootScope.public.node.css) {
          elem = document.getElementById("load-custom-css");
          if (elem === null) {
            elem = document.createElement("link");
            elem.setAttribute("id", "load-custom-css");
            elem.setAttribute("rel", "stylesheet");
            elem.setAttribute("type", "text/css");
            elem.setAttribute("href", "s/css");
            document.getElementsByTagName("head")[0].appendChild(elem);
          }
        }

	if ($rootScope.public.node.script) {
          elem = document.getElementById("load-custom-script");
          if (elem === null) {
            elem = document.createElement("script");
            elem.setAttribute("id", "load-custom-script");
            elem.setAttribute("type", "text/javascript");
            elem.setAttribute("src", "s/script");
            document.getElementsByTagName("body")[0].appendChild(elem);
          }
        }

        $rootScope.contexts_by_id = $rootScope.Utils.array_to_map(result.contexts);
        $rootScope.receivers_by_id = $rootScope.Utils.array_to_map(result.receivers);
        $rootScope.questionnaires_by_id = $rootScope.Utils.array_to_map(result.questionnaires);

        $rootScope.submission_statuses = result.submission_statuses;
        $rootScope.submission_statuses_by_id = $rootScope.Utils.array_to_map(result.submission_statuses);

        angular.forEach($rootScope.questionnaires_by_id, function(element, key) {
          $rootScope.fieldUtilities.parseQuestionnaire($rootScope.questionnaires_by_id[key], {});
          $rootScope.questionnaires_by_id[key].steps = $filter("orderBy")($rootScope.questionnaires_by_id[key].steps, "order");
        });

        angular.forEach($rootScope.contexts_by_id, function(element, key) {
          $rootScope.contexts_by_id[key].questionnaire = $rootScope.questionnaires_by_id[$rootScope.contexts_by_id[key].questionnaire_id];
          if ($rootScope.contexts_by_id[key].additional_questionnaire_id) {
            $rootScope.contexts_by_id[key].additional_questionnaire = $rootScope.questionnaires_by_id[$rootScope.contexts_by_id[key].additional_questionnaire_id];
          }
        });

        $rootScope.connection = {
          "https": $location.protocol() === "https",
          "tor": getResponseHeaders()["X-Check-Tor"] === "true" || $location.host().match(/\.onion$/),
        };

        $rootScope.privacy_badge_open = !$rootScope.connection.tor;

        Utils.route_check();

        $rootScope.languages_enabled = {};
        $rootScope.languages_enabled_selector = [];
        $rootScope.languages_supported = {};
        angular.forEach($rootScope.public.node.languages_supported, function(lang) {
          $rootScope.languages_supported[lang.code] = lang;
          if ($rootScope.public.node.languages_enabled.indexOf(lang.code) !== -1) {
            $rootScope.languages_enabled[lang.code] = lang;
            $rootScope.languages_enabled_selector.push(lang);
          }
        });

        if ($rootScope.public.node.enable_experimental_features) {
          $rootScope.isFieldTriggered = fieldUtilities.isFieldTriggered;
        } else {
          $rootScope.isFieldTriggered = $rootScope.null_function;
        }

        $rootScope.evaluateConfidentialityModalOpening();

        GLTranslate.addNodeFacts($rootScope.public.node.default_language, $rootScope.public.node.languages_enabled);
        Utils.set_title();

        $rootScope.started = true;

        var observer = new MutationObserver(GL.mockEngine.run);

        observer.observe(document.querySelector("body"), { attributes: false, childList: true, subtree: true });
      }).$promise;
    };

    //////////////////////////////////////////////////////////////////

    $rootScope.$watch(function() {
      return $http.pendingRequests.length;
    }, function(val) {
      $rootScope.showLoadingPanel = val > 0;
    });

    $rootScope.$watch("GLTranslate.state.language", function(new_val, old_val) {
      if(new_val !== old_val) {
        GLTranslate.setLang(new_val);
	$rootScope.reload();
      }
    });

    $rootScope.$on("$locationChangeStart", function() {
      var lang = $location.search().lang;

      if ($location.path() === "/" &&
          $rootScope.Authentication.session &&
          $rootScope.Authentication.session.role !== "whistleblower") {
        // Get suer to reset the user session when visiting the public interface
	// This is intended as protection in relation to possible XSS and XSRF
	// on components implementing markdown and direct html input.
        $rootScope.Authentication.session = undefined;
      }

      if(lang && lang !== GLTranslate.state.language) {
	$window.location.href = $location.absUrl();
	$window.location.reload();
      }
    });

    $rootScope.$on("$routeChangeStart", Utils.route_check);

    $rootScope.$on("$routeChangeSuccess", function (event, current) {
      if (current.$$route) {
        $rootScope.errors.length = 0;
        $rootScope.header_title = current.$$route.header_title;
        $rootScope.sidebar = current.$$route.sidebar;
	Utils.set_title();
      }

      $rootScope.location_path = $location.path();
    });

    $rootScope.$on("$routeChangeError", function(event, current, previous, rejection) {
      if (rejection === Access.FORBIDDEN) {
        $rootScope.Authentication.loginRedirect(false);
      }
    });

    $rootScope.$on("REFRESH", function() {
      $rootScope.reload();
    });

    $rootScope.keypress = function(e) {
       if (((e.which || e.keyCode) === 116) || /* F5 */
           ((e.which || e.keyCode) === 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */
         e.preventDefault();
         $rootScope.$emit("REFRESH");
       }
    };

    $rootScope.reload = function(new_path) {
      $rootScope.errors.length = 0;
      $rootScope.init().then(function() {
        $route.reload();

        if (new_path) {
          $location.path(new_path).replace();
        }
      });
    };

    $rootScope.init();
}]).
  factory("globaleaksRequestInterceptor", ["$injector", function($injector) {
    return {
     "request": function(config) {
       var $rootScope = $injector.get("$rootScope");

       angular.extend(config.headers, $rootScope.Authentication.get_headers());

       return config;
     },
     "responseError": function(response) {
       /*/
          When the response has failed write the rootScope
          errors array the error message.
       */
       var $rootScope = $injector.get("$rootScope");
       var $http = $injector.get("$http");
       var $q = $injector.get("$q");
       var $location = $injector.get("$location");

       if (response.status === 405) {
         var errorData = angular.toJson({
           errorUrl: $location.path(),
           errorMessage: response.statusText,
           stackTrace: [{
             "url": response.config.url,
             "method": response.config.method
           }],
           agent: navigator.userAgent
         });
         $http.post("api/exception", errorData);
       }

       if (response.data !== null) {
         var error = {
           "message": response.data.error_message,
           "code": response.data.error_code,
           "arguments": response.data.arguments
         };

         /* 10: Not Authenticated */
         if (error.code === 10) {
           $rootScope.Authentication.loginRedirect(false);
         } else if (error.code === 4) {
           $rootScope.Authentication.authcoderequired = true;
         } else {
           $rootScope.errors.push(error);
         }
       }

       return $q.reject(response);
     }
   };
}]).
  factory("noopInterpolation", ["$interpolate", "$translateSanitization", function ($interpolate, $translateSanitization) {
  // simple noop interpolation service

  var $locale,
      $identifier = "noop";

  return {
    setLocale: function(locale) {
      $locale = locale;
    },
    getInterpolationIdentifier : function () {
      return $identifier;
    },
    useSanitizeValueStrategy: function (value) {
      $translateSanitization.useStrategy(value);
      return this;
    },
    interpolate: function (value/*, interpolationParams, context, sanitizeStrategy, translationId*/) {
      return value;
    }
  };
}]).
  factory("stacktraceService", function() {
    return({
      fromError: StackTrace.fromError
    });
});
