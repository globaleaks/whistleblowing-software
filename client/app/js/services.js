angular.module("GLServices", ["ngResource"]).
  factory("Test", function () {
    return false;
  }).
  factory("GLResource", ["$resource", function($resource) {
    return function(url, params, actions) {
      var defaults = {
        get:    {method: "get"},
        query:  {method: "get", isArray: true},
        update: {method: "put"}
      };

      actions = angular.extend(defaults, actions);

      return $resource(url, params, actions);
    };
  }]).
  factory("Authentication",
    ["$filter", "$http", "$location", "$window", "$routeParams", "$rootScope", "GLTranslate", "UserPreferences", "ReceiverPreferences",
    function($filter, $http, $location, $window, $routeParams, $rootScope, GLTranslate, UserPreferences, ReceiverPreferences) {
      function Session(){
        var self = this;

        self.loginInProgress = false;

        self.set_session = function(response) {
          response = response.data;

          self.session = {
            "id": response.session_id,
            "user_id": response.user_id,
            "role": response.role,
            "password_change_needed": response.password_change_needed,
            "homepage": "",
            "auth_landing_page": ""
          };

          function initPreferences(prefs) {
            $rootScope.preferences = prefs;
            GLTranslate.addUserPreference(prefs.language);
          }

          if (self.session.role === "admin") {
            self.session.homepage = "#/admin/home";
            self.session.auth_landing_page = "/admin/home";
            UserPreferences.get().$promise.then(initPreferences);
          } else if (self.session.role === "custodian") {
            self.session.homepage = "#/custodian/home";
            self.session.auth_landing_page = "/custodian/home";
            UserPreferences.get().$promise.then(initPreferences);
          } else if (self.session.role === "receiver") {
            self.session.homepage = "#/receiver/home";
            self.session.auth_landing_page = "/receiver/home";
            ReceiverPreferences.get().$promise.then(initPreferences);
          } else if (self.session.role === "whistleblower") {
            self.session.auth_landing_page = "/status";
            self.session.homepage = "#/status";
          }

          self.session.role_l10n = function() {
            return $filter("translate")(self.session.role.charAt(0).toUpperCase() + self.session.role.substr(1));
          };
        };

        self.login = function(tid, username, password, authcode, token, cb) {
          if (authcode === undefined) {
              authcode = "";
          }

          self.loginInProgress = true;

          var success_fn = function(response) {
            // reset login status before returning
            self.loginInProgress = false;

            if ("redirect" in response.data) {
              if ($rootScope.embedded && $rootScope.node.allows_iframes_inclusion) {
                $window.parent.postMessage({"cmd": "redirect", "data": response.data["redirect"]}, "*");
              } else {
                $window.location.replace(response.data["redirect"]);
              }
            }

            self.set_session(response);

            if ($routeParams.src) {
              $location.path($routeParams.src);
            } else {
              // Override the auth_landing_page if a password change is needed
              if (self.session.password_change_needed) {
                // Redirect UI to the ForcedPasswordChange view
                $location.path("/forcedpasswordchange");
              } else {
                $location.path(self.session.auth_landing_page);
              }
            }

            $location.search("");

            if (cb){
              return cb();
            }
          };

          if (username === "whistleblower") {
            password = password.replace(/\D/g,"");
            return $http.post("receiptauth", {"receipt": password}).
            then(success_fn, function() {
              self.loginInProgress = false;
            });
          } else if (token) {
            return $http.post("tokenauth", {"tid": tid, "token": token}).
            then(success_fn, function() {
              self.loginInProgress = false;
            });
          } else {
            return $http.post("authentication", {"tid": tid, "username": username, "password": password, "authcode": authcode}).
            then(success_fn, function() {
              self.loginInProgress = false;
            });
          }
        };

        self.getLoginUri = function (role, path) {
          var loginUri = "/login";

          if (role === undefined ) {
            if (path === "/status") {
              loginUri = "/";
            } else if (path.indexOf("/admin") === 0) {
              loginUri = "/admin";
            } else if (path.indexOf("/custodian") === 0) {
              loginUri = "/login";
            }
          } else if (role === "whistleblower") {
            loginUri = ("/");
          } else if (role === "admin") {
            loginUri = "/admin";
          } else if (role === "custodian") {
            loginUri = "/login";
          }

          return loginUri;
        };

        self.receipt = "";

        self.logout = function() {
          var logoutPerformed = function() {
            self.loginRedirect(true);
          };

          $http.delete("session").then(logoutPerformed,
                                       logoutPerformed);
        };

        self.loginRedirect = function(isLogout) {
          var role = self.session === undefined ? undefined : self.session.role;

          self.session = undefined;

          var source_path = $location.path();

          var redirect_path = self.getLoginUri(role, source_path);

          // Only redirect if we are not already on the login page
          if (source_path !== redirect_path) {
            $location.path(redirect_path);
            if (!isLogout) {
              $location.search("src=" + source_path);
            }
          }
        };

        self.hasUserRole = function() {
          if (angular.isUndefined(self.session)) {
            return false;
          }
          var r = self.session.role;
          return (r === "admin" || r === "receiver" || r === "custodian");
        };

        self.get_headers = function() {
          var h = {};

          if (self.session) {
            h["X-Session"] = self.session.id;
          }

          if (GLTranslate.state.language !== null) {
            h["GL-Language"] = GLTranslate.state.language;
          }

          return h;
        };
      }

      return new Session();
}]).
factory("Access", ["$q", "Authentication", function ($q, Authentication) {
  var Access = {
    OK: 200,

    FORBIDDEN: 403,

    isUnauth: function () {
      if (Authentication.session === undefined) {
        return $q.resolve(Access.OK);
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    },

    isAuthenticated: function (role) {
      // acl is a special auth level meaning that access is conditional on
      // backend flags and the only way to know for sure if a given op will
      // work is to test

      if (Authentication.session && (role === "*" || role === "acl" || Authentication.session.role === role)) {
        return $q.resolve(Access.OK);
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    }
  };

  return Access;
}]).
  factory("PublicResource", ["GLResource", function(GLResource) {
    return new GLResource("public");
}]).
  factory("TokenResource", ["GLResource", function(GLResource) {
    return new GLResource("token/:id", {id: "@id"});
}]).
  factory("SubmissionResource", ["GLResource", function(GLResource) {
    return new GLResource("submission/:id", {id: "@token_id"});
}]).
  factory("FieldAttrs", ["$resource", function($resource) {
    return $resource("data/field_attrs.json");
}]).
  factory("DATA_COUNTRIES_ITALY_REGIONS", ["$resource", function($resource) {
    return $resource("data/countries/it/regioni.json");
}]).
  factory("DATA_COUNTRIES_ITALY_PROVINCES", ["$resource", function($resource) {
    return $resource("data/countries/it/province.json");
}]).
  factory("DATA_COUNTRIES_ITALY_CITIES", ["$resource", function($resource) {
    return $resource("data/countries/it/comuni.json");
}]).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory("Submission", ["$q", "GLResource", "$filter", "$location", "$rootScope", "Authentication", "TokenResource", "SubmissionResource",
      function($q, GLResource, $filter, $location, $rootScope, Authentication, TokenResource, SubmissionResource) {

    return function(fn) {
      /**
       * This factory returns a Submission object that will call the fn
       * callback once all the information necessary for creating a submission
       * has been collected.
       *
       * This means getting the node information, the list of receivers and the
       * list of contexts.
       */
      var self = this;

      self._submission = null;
      self.context = undefined;
      self.receivers = [];
      self.selected_receivers = {};
      self.done = false;

      self.isDisabled = function() {
        return self.count_selected_receivers() === 0 ||
               self.wait ||
               !self.pow ||
               self.done;
      };

      self.count_selected_receivers = function () {
        var count = 0;

        angular.forEach(self.selected_receivers, function (selected) {
          if (selected) {
            count += 1;
          }
        });

        return count;
      };

      self.setContextReceivers = function(context_id) {
        self.context = $rootScope.contexts_by_id[context_id];

        // bypass the re-initialization if recipients are manually selected
        if (Object.keys(self.selected_receivers).length && self.context.allow_recipients_selection) {
          return;
        }

        self.selected_receivers = {};
        self.receivers = [];

        angular.forEach($rootScope.receivers, function(receiver) {
          if (self.context.receivers.indexOf(receiver.id) !== -1) {
            self.receivers.push(receiver);

            if (receiver.pgp_key_public !== "" || $rootScope.node.allow_unencrypted) {
              if (receiver.recipient_configuration === "default") {
                self.selected_receivers[receiver.id] = self.context.select_all_receivers;
              } else if (receiver.recipient_configuration === "forcefully_selected") {
                self.selected_receivers[receiver.id] = true;
              }
            }
          }
        });
      };

      /**
       * @name Submission.create
       * @description
       * Create a new submission based on the currently selected context.
       *
       * */
      self.create = function(context_id, cb) {
        self.setContextReceivers(context_id);

        self._submission = new SubmissionResource({
          context_id: self.context.id,
          receivers: [],
          identity_provided: false,
          answers: {},
          answer: 0,
          total_score: 0,
          mobile: $rootScope.mobile
        });

        self._token = new TokenResource({"type": "submission"}).$save(function(token) {
          self._token = token;
          self._submission.token_id = self._token.id;

          if (cb) {
            cb();
          }
        });
      };

      /**
       * @name Submission.submit
       * @description
       * Submit the currently configured submission.
       * This involves setting the receivers of the submission object to those
       * currently selected and setting up the submission fields entered by the
       * whistleblower.
       */
      self.submit = function() {
        self.done = true;

        self._submission.receivers = [];
        angular.forEach(self.selected_receivers, function(selected, id){
          if (selected) {
            self._submission.receivers.push(id);
          }
        });

        self._submission.$update(function(result){
          if (result) {
            Authentication.submission = self._submission;
            Authentication.context = self.context;
            $location.url("/receipt");
          }
        });

      };

      fn(self);
    };
}]).
  factory("RTipResource", ["GLResource", function(GLResource) {
    return new GLResource("rtip/:id", {id: "@id"});
}]).
  factory("RTipCommentResource", ["GLResource", function(GLResource) {
    return new GLResource("rtip/:id/comments", {id: "@id"});
}]).
  factory("RTipMessageResource", ["GLResource", function(GLResource) {
    return new GLResource("rtip/:id/messages", {id: "@id"});
}]).
  factory("RTipIdentityAccessRequestResource", ["GLResource", function(GLResource) {
    return new GLResource("rtip/:id/identityaccessrequests", {id: "@id"});
}]).
  factory("RTipDownloadRFile", ["$http", "FileSaver", function($http, FileSaver) {
    return function(file) {
      return $http({
        method: "GET",
        url: "rtip/rfile/" + file.id,
        responseType: "blob",
      }).then(function (response) {
        FileSaver.saveAs(response.data, file.name);
      });
    };
}]).
  factory("RTipWBFileResource", ["GLResource", function(GLResource) {
    return new GLResource("rtip/wbfile/:id", {id: "@id"});
}]).
  factory("RTipDownloadWBFile", ["$http", "FileSaver", function($http, FileSaver) {
    return function(file) {
      return $http({
        method: "GET",
        url: "rtip/wbfile/" + file.id,
        responseType: "blob",
      }).then(function (response) {
        FileSaver.saveAs(response.data, file.name);
      });
    };
}]).
  factory("RTipExport", ["$http", "$filter", "FileSaver", function($http, $filter, FileSaver) {
    return function(tip) {
      $http({
        method: "GET",
        url: "rtip/" + tip.id + "/export",
        responseType: "blob",
      }).then(function (response) {
        var filename = "submission-" + tip.progressive + ".zip";
        FileSaver.saveAs(response.data, filename);
      });
    };
}]).
  factory("RTip", ["$rootScope", "$http", "$filter", "RTipResource", "RTipMessageResource", "RTipCommentResource",
          function($rootScope, $http, $filter, RTipResource, RTipMessageResource, RTipCommentResource) {
    return function(tipID, fn) {
      var self = this;

      self.tip = RTipResource.get(tipID, function (tip) {
        tip.context = $rootScope.contexts_by_id[tip.context_id];
        tip.questionnaire = $rootScope.questionnaires_by_id[tip.context.questionnaire_id];
        tip.additional_questionnaire = $rootScope.questionnaires_by_id[tip.context.additional_questionnaire_id];

        tip.iars = $filter("orderBy")(tip.iars, "request_date");
        tip.last_iar = tip.iars.length > 0 ? tip.iars[tip.iars.length - 1] : null;

        tip.newComment = function(content) {
          var c = new RTipCommentResource(tipID);
          c.content = content;
          c.$save(function(newComment) {
            tip.comments.unshift(newComment);
            tip.localChange();
          });
        };

        tip.newMessage = function(content) {
          var m = new RTipMessageResource(tipID);
          m.content = content;
          m.$save(function(newMessage) {
            tip.messages.unshift(newMessage);
            tip.localChange();
          });
        };

        tip.operation = function(operation, args) {
          var req = {
            "operation": operation,
            "args": args
          };

          return $http({method: "PUT", url: "rtip/" + tip.id, data: req});
        };

        tip.updateLabel = function(label) {
          return tip.operation("update_label", {"value": label}).then(function () {
            tip["label"] = label;
          });
        };

        tip.updateSubmissionStatus = function() {
          var status = tip.submissionStatusObj.id;
          var substatus = tip.submissionSubStatusObj ? tip.submissionSubStatusObj.id : "";
          return tip.operation("update_status", {"status": status,
                                                 "substatus": substatus}).then(function () {
            tip.status = status;
            tip.substatus = substatus;
          });
        };

        tip.localChange = function() {
          tip.update_date = (new Date()).toISOString();
        };

        if (fn) {
          fn(tip);
        }
      });
    };
}]).
  factory("WBTipResource", ["GLResource", function(GLResource) {
    return new GLResource("wbtip");
}]).
  factory("WBTipCommentResource", ["GLResource", function(GLResource) {
    return new GLResource("wbtip/comments");
}]).
  factory("WBTipMessageResource", ["GLResource", function(GLResource) {
    return new GLResource("wbtip/messages/:id", {id: "@id"});
}]).
  factory("WBTipDownloadFile", ["$http", "FileSaver", function($http, FileSaver) {
    return function(file) {
      return $http({
        method: "GET",
        url: "wbtip/wbfile/" + file.id,
        responseType: "blob",
      }).then(function (response) {
        FileSaver.saveAs(response.data, file.name);
      });
    };
}]).
  factory("WBTip", ["$rootScope", "$filter", "WBTipResource", "WBTipCommentResource", "WBTipMessageResource",
      function($rootScope, $filter, WBTipResource, WBTipCommentResource, WBTipMessageResource) {
    return function(fn) {
      var self = this;

      self.tip = WBTipResource.get(function (tip) {
        tip.context = $rootScope.contexts_by_id[tip.context_id];
        tip.questionnaire = $rootScope.questionnaires_by_id[tip.context.questionnaire_id];
        tip.additional_questionnaire = $rootScope.questionnaires_by_id[tip.context.additional_questionnaire_id];

        tip.msg_receiver_selected = null;
        tip.msg_receivers_selector = [];

        angular.forEach(tip.receivers, function(r) {
          if($rootScope.receivers_by_id[r.id]) {
            r = $rootScope.receivers_by_id[r.id];
            tip.msg_receivers_selector.push({
              key: r.id,
              value: r.name
            });
          }
        });

        tip.newComment = function(content) {
          var c = new WBTipCommentResource();
          c.content = content;
          c.$save(function(newComment) {
            tip.comments.unshift(newComment);
            tip.localChange();
          });
        };

        tip.newMessage = function(content) {
          var m = new WBTipMessageResource({id: tip.msg_receiver_selected});
          m.content = content;
          m.$save(function(newMessage) {
            tip.messages.unshift(newMessage);
            tip.localChange();
          });
        };

        tip.localChange = function() {
          tip.update_date = (new Date()).toISOString();
        };

        if (fn) {
          fn(tip);
        }
      });
    };
}]).
  factory("ReceiverPreferences", ["GLResource", function(GLResource) {
    return new GLResource("receiver/preferences");
}]).
  factory("ReceiverTips", ["GLResource", function(GLResource) {
    return new GLResource("receiver/tips");
}]).
  factory("IdentityAccessRequests", ["GLResource", function(GLResource) {
    return new GLResource("custodian/identityaccessrequests");
}]).
  factory("ManifestResource", ["$resource", function($resource) {
    return new $resource("admin/manifest");
}]).
  factory("AdminContextResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/contexts/:id", {id: "@id"});
}]).
  factory("AdminQuestionnaireResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/questionnaires/:id", {id: "@id"});
}]).
  factory("AdminStepResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/steps/:id", {id: "@id"});
}]).
  factory("AdminFieldResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/fields/:id",{id: "@id"});
}]).
  factory("AdminFieldTemplateResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/fieldtemplates/:id", {id: "@id"});
}]).
  factory("AdminRedirectResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/redirects/:id", {id: "@id"});
}]).
  factory("AdminTenantResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/tenants/:id", {id: "@id"});
}]).
  factory("AdminUserResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/users/:id", {id: "@id"});
}]).
  factory("AdminSubmissionStatusResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/submission_statuses/:id", {id: "@id"});
}]).
factory("AdminSubmissionSubStatusResource", ["GLResource", function(GLResource) {
  return new GLResource("admin/submission_statuses/:submissionstatus_id/substatuses/:id", {id: "@id", submissionstatus_id: "@submissionstatus_id"});
}]).
factory("AdminUserTenantAssociationResource", ["GLResource", function(GLResource) {
  return new GLResource("admin/users/:user_id/tenant_associations/:tenant_id", {user_id: "@user_id", tenant_id: "@tenant_id"});
}]).
factory("Sites", ["GLResource", function(GLResource) {
    return new GLResource("sites");
}]).
service("UpdateService", [function() {
  return {
    new_data: function(installed_version, latest_version) {
      this.latest_version = latest_version;
      if (this.latest_version !== installed_version) {
        this.update_needed = true;
      }
    },
    update_needed: false,
    latest_version: undefined,
  };
}]).
  factory("AdminNodeResource", ["GLResource", "UpdateService", function(GLResource, UpdateService) {
    return new GLResource("admin/node", {}, {
      get: {
        method: "get",
        interceptor: {
          response: function(response) {
            UpdateService.new_data(response.resource.version, response.resource.latest_version);
            return response.resource;
          },
        },
      },
  });
}]).
  factory("AdminNotificationResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/notification");
}]).
  factory("AdminL10NResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/l10n/:lang", {lang: "@lang"});
}]).
factory("AdminTLSConfigResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/config/tls", {}, {
        "enable":  { method: "POST", params: {}},
        "disable": { method: "PUT", params: {}},
    });
}]).
factory("AdminTLSCertFileResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/config/tls/files");
}]).
factory("AdminAcmeResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/config/acme/run");
}]).
factory("AdminTLSCfgFileResource", ["GLResource", function(GLResource) {
    return new GLResource("admin/config/tls/files/:name", {name: "@name"});
}]).
factory("AdminUtils", ["AdminContextResource", "AdminQuestionnaireResource", "AdminStepResource", "AdminFieldResource", "AdminFieldTemplateResource", "AdminUserResource", "AdminNodeResource", "AdminNotificationResource", "AdminRedirectResource", "AdminTenantResource",
    function(AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminNodeResource, AdminNotificationResource, AdminRedirectResource, AdminTenantResource) {
  return {
    new_context: function() {
      var context = new AdminContextResource();
      context.id = "";
      context.status = 2;
      context.name = "";
      context.description = "";
      context.presentation_order = 0;
      context.tip_timetolive = 15;
      context.show_recipients_details = false;
      context.allow_recipients_selection = false;
      context.show_receivers_in_alphabetical_order = true;
      context.show_steps_navigation_interface = true;
      context.select_all_receivers = true;
      context.maximum_selectable_receivers = 0;
      context.show_small_receiver_cards = false;
      context.enable_comments = true;
      context.enable_messages = false;
      context.enable_two_way_comments = true;
      context.enable_two_way_messages = true;
      context.enable_attachments = true;
      context.enable_rc_to_wb_files = false;
      context.recipients_clarification = "";
      context.status_page_message = "";
      context.questionnaire_id = "";
      context.additional_questionnaire_id = "";
      context.score_threshold_medium = 0;
      context.score_threshold_high = 0;
      context.score_receipt_text_custom = false;
      context.score_receipt_text_l = "";
      context.score_receipt_text_m = "";
      context.score_receipt_text_h = "";
      context.score_threshold_receipt = 0;
      context.receivers = [];
      return context;
    },

    new_questionnaire: function() {
      var questionnaire = new AdminQuestionnaireResource();
      questionnaire.id = "";
      questionnaire.key = "";
      questionnaire.name = "";
      questionnaire.steps = [];
      questionnaire.editable = true;
      return questionnaire;
    },

    new_step: function(questionnaire_id) {
      var step = new AdminStepResource();
      step.id = "";
      step.label = "";
      step.description = "";
      step.presentation_order = 0;
      step.children = [];
      step.questionnaire_id = questionnaire_id;
      step.triggered_by_score = 0;
      step.triggered_by_options = [];
      return step;
    },

    new_field: function(step_id, fieldgroup_id) {
      var field = new AdminFieldResource();
      field.id = "";
      field.key = "";
      field.instance = "instance";
      field.editable = true;
      field.descriptor_id = "";
      field.label = "";
      field.type = "inputbox";
      field.description = "";
      field.hint = "";
      field.placeholder = "";
      field.multi_entry = false;
      field.multi_entry_hint = "";
      field.required = false;
      field.preview = false;
      field.encrypt = true;
      field.attrs = {};
      field.options = [];
      field.x = 0;
      field.y = 0;
      field.width = 0;
      field.children = [];
      field.fieldgroup_id = fieldgroup_id;
      field.step_id = step_id;
      field.template_id = "";
      field.template_override_id = "";
      field.triggered_by_score = 0;
      field.triggered_by_options = [];
      return field;
    },

    new_field_template: function (fieldgroup_id) {
      var field = new AdminFieldTemplateResource();
      field.id = "";
      field.key = "";
      field.instance = "template";
      field.editable = true;
      field.label = "";
      field.type = "inputbox";
      field.description = "";
      field.placeholder = "";
      field.hint = "";
      field.multi_entry = false;
      field.multi_entry_hint = "";
      field.required = false;
      field.preview = false;
      field.encrypt = false;
      field.attrs = {};
      field.options = [];
      field.x = 0;
      field.y = 0;
      field.width = 0;
      field.children = [];
      field.fieldgroup_id = fieldgroup_id;
      field.step_id = "";
      field.template_id = "";
      field.template_override_id = "";
      field.triggered_by_score = 0;
      field.triggered_by_options = [];
      return field;
    },

    new_user: function () {
      var user = new AdminUserResource();
      user.id = "";
      user.username = "";
      user.role = "receiver";
      user.state = "enable";
      user.password = "";
      user.old_password = "";
      user.password_change_needed = true;
      user.state = "enabled";
      user.name = "";
      user.description = "";
      user.mail_address = "";
      user.pgp_key_fingerprint = "";
      user.pgp_key_remove = false;
      user.pgp_key_public = "";
      user.pgp_key_expiration = "";
      user.language = "en";
      user.notification = true;
      user.recipient_configuration = "default";
      user.can_edit_general_settings = false;
      user.can_delete_submission = false;
      user.can_postpone_expiration = false;
      user.can_grant_permissions = false;
      return user;
    },

    new_redirect: function () {
      return new AdminRedirectResource();
    },

    new_tenant: function() {
      var tenant = new AdminTenantResource();
      tenant.active = true;
      tenant.label = "";
      tenant.mode = "default";
      tenant.subdomain = "";
      return tenant;
    },
  };
}]).
  factory("UserPreferences", ["GLResource", function(GLResource) {
    return new GLResource("preferences", {}, {"update": {method: "PUT"}});
}]).
  factory("JobsOverview", ["GLResource", function(GLResource) {
    return new GLResource("admin/jobs");
}]).
  factory("StatsCollection", ["GLResource", function(GLResource) {
    return new GLResource("admin/stats/:week_delta", {week_delta: "@week_delta"}, {});
}]).
  factory("AnomaliesCollection", ["GLResource", function(GLResource) {
    return new GLResource("admin/anomalies");
}]).
  factory("ActivitiesCollection", ["GLResource", function(GLResource) {
    return new GLResource("admin/activities/details");
}]).
  factory("Files", ["GLResource", function(GLResource) {
    return new GLResource("admin/files");
}]).
  factory("DefaultL10NResource", ["GLResource", function(GLResource) {
    return new GLResource("l10n/:lang.json", {lang: "@lang"});
}]).
  factory("Utils", ["$rootScope", "$http", "$q", "$location", "$filter", "$sce", "$uibModal", "$window", "Authentication",
  function($rootScope, $http, $q, $location, $filter, $sce, $uibModal, $window, Authentication) {
    return {
      array_to_map: function(array) {
        var ret = {};
        angular.forEach(array, function(element) {
          ret[element.id] = element;
        });
        return ret;
      },

      set_title: function() {
        var nodename = $rootScope.node.name ? $rootScope.node.name : "Globaleaks";
        var path = $location.path();
        var statuspage = "/status";

        if (path === "/") {
          $rootScope.ht = $rootScope.node.header_title_homepage;
        } else if (path === "/submission") {
          $rootScope.ht = $rootScope.node.header_title_submissionpage;
        } else if (path.substr(0, statuspage.length) === statuspage) {
          $rootScope.ht = $rootScope.node.header_title_tippage;
        } else {
          $rootScope.ht = $rootScope.header_title;
        }

        $rootScope.ht = $filter("translate")($rootScope.ht);

        $rootScope.pt = ($rootScope.ht !== "" && $rootScope.ht !== nodename) ? nodename + " - " + $rootScope.ht : nodename;
      },

      route_check: function() {
        if (!$rootScope.node.wizard_done) {
          $location.path("/wizard");
        } else if ($location.path() === "/" && $rootScope.node.enable_signup) {
          $location.path("/signup");
        } else if ($location.path() !== "/signup" && $rootScope.node.adminonly && !$rootScope.Authentication.session) {
          $location.path("/admin");
        } else  if ($location.path() === "/" && $rootScope.node.landing_page === "submissionpage") {
          $location.path("/submission");
        } else if ($location.path() === "/submission" &&
            !$rootScope.connection.tor &&
            !$rootScope.node.https_whistleblower) {
          $location.path("/");
        }
      },

      getXOrderProperty: function() {
        return "x";
      },

      getYOrderProperty: function(elem) {
        var key = "presentation_order";
        if (elem[key] === undefined) {
          key = "y";
        }
        return key;
      },

      dumb_function: function() {
        return true;
      },

      b64DecodeUnicode: function(str) {
        // https://github.com/globaleaks/GlobaLeaks/issues/2079
        // https://developer.mozilla.org/en-US/docs/Web/API/WindowBase64/Base64_encoding_and_decoding
        // Going backwards: from bytestream, to percent-encoding, to original string.
        return decodeURIComponent(atob(str).split("").map(function(c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(""));
      },

      iframeCheck: function() {
        try {
          return window.self !== window.top;
        } catch (e) {
          return true;
        }
      },

      base64ToTrustedScriptUrl: function(base64_data) {
        return $sce.trustAsResourceUrl("data:application/javascript;base64," + base64_data);
      },

      update: function (model, cb, errcb) {
        var success = {};
        model.$update(
          function() {
            $rootScope.successes.push(success);
            if (cb !== undefined) { cb(); }
          },
          function() {
            if (errcb !== undefined) {
              errcb();
            }
          }
        );
      },

      go: function (path) {
        $location.path(path);
      },

      randomFluff: function () {
        return Math.random() * 1000000 + 1000000;
      },

      imgDataUri: function(data) {
        if (data === "") {
          data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgDTD2qgAAAAASUVORK5CYII=";
        }

        return "data:image/png;base64," + data;
      },

      attachCustomJS: function() {
        return angular.isDefined($rootScope.node) && angular.isDefined($rootScope.node.script);
      },

      isWhistleblowerPage: function() {
        var path = $location.path();
        return (path === "/" ||
                path === "/start" ||
                path === "/submission" ||
                path === "/receipt" ||
                path === "/status");
      },

      classExtension: function() {
        return {
          "ext-public": this.isWhistleblowerPage(),
          "ext-authenticated": Authentication.hasUserRole(),
          "ext-embedded": $rootScope.embedded,
        };
      },

      showLoginForm: function () {
        return $location.path() === "/submission";
      },

      showUserStatusBox: function() {
        return angular.isDefined($rootScope.session);
      },

      showPrivacyBadge: function() {
        return (!$rootScope.embedded &&
                !$rootScope.node.disable_privacy_badge &&
                this.isWhistleblowerPage());
      },

      showFilePreview: function(content_type) {
        var content_types = [
          "image/gif",
          "image/jpeg",
          "image/png",
          "image/bmp"
        ];

        return content_types.indexOf(content_type) > -1;
      },

      moveUp: function(elem) {
        elem[this.getYOrderProperty(elem)] -= 1;
      },

      moveDown: function(elem) {
        elem[this.getYOrderProperty(elem)] += 1;
      },

      moveLeft: function(elem) {
        elem[this.getXOrderProperty(elem)] -= 1;
      },

      moveRight: function(elem) {
        elem[this.getXOrderProperty(elem)] += 1;
      },

      deleteFromList: function(list, elem) {
        var idx = list.indexOf(elem);
        if (idx !== -1) {
          list.splice(idx, 1);
        }
      },

      deleteFromDict: function(dict, key) {
          delete dict[key];
      },

      assignUniqueOrderIndex: function(elements) {
        if (elements.length <= 0) {
          return;
        }

        var key = this.getYOrderProperty(elements[0]);
        if (elements.length) {
          var i = 0;
          elements = $filter("orderBy")(elements, key);
          angular.forEach(elements, function (element) {
            element[key] = i;
            i += 1;
          });
        }
      },

      getUploadStatus: function(uploads) {
        if (uploads.progress() !== 1) {
          return "uploading";
        }

        return "finished";
      },

      isUploading: function(uploads) {
        for (var key in uploads) {
          if (uploads[key].files.length > 0 && uploads[key].progress() !== 1) {
            return true;
          }
        }

        return false;
      },

      openConfirmableModalDialog: function(template, arg, scope) {
        scope = !scope ? $rootScope : scope;

        var modal = $uibModal.open({
          templateUrl: template,
          controller: "ConfirmableDialogCtrl",
          backdrop: "static",
          keyboard: false,
          scope: scope,
          resolve: {
            arg: function () {
              return arg;
            }
          }
        });

        return modal.result;
      },

      deleteDialog: function() {
        return this.openConfirmableModalDialog("views/partials/delete_dialog.html");
      },

      deleteResource: function(factory, list, res) {
        factory.delete({
          id: res.id
        }, function() {
          list.splice(list.indexOf(res), 1);
        });
      },

      isNever: function(time) {
        var date = new Date(time);
        return date.getTime() === 32503680000000;
      },

      getPostponeDate: function(ttl) {
        var date = new Date();
        date.setDate(date.getDate() + ttl + 1);
        date.setUTCHours(0, 0, 0, 0);
        return date;
      },

      readFileAsText: function (file) {
        var deferred = $q.defer();

        var reader = new $window.FileReader();

        reader.onload = function (e) {
          deferred.resolve(e.target.result);
        };

        reader.readAsText(file);

        return deferred.promise;
      },

      readFileAsJson: function (file) {
        return this.readFileAsText(file).then(function(txt) {
          try {
            return JSON.parse(txt);
          } catch (excep) {
            return $q.reject(excep);
          }
        });
      },

      displayErrorMsg: function(reason) {
        var error = {
          "message": "local-failure",
          "arguments": [reason],
          "code": 10,
        };
        $rootScope.errors.push(error);
      },

      evalSubmissionStatus: function(tip, submission_statuses) {
        for (var i = 0; i < submission_statuses.length; i++) {
          if (submission_statuses[i].id === tip.status) {
            tip.submissionStatusObj = submission_statuses[i];

            var substatuses = submission_statuses[i].substatuses;
            for (var j = 0; j < substatuses.length; j++) {
              if (substatuses[j].id === tip.substatus) {
                tip.submissionSubStatusObj = substatuses[j];
                break;
              }
            }
            break;
          }
        }

        tip.submissionStatusStr = $filter("translate")(tip.submissionStatusObj.label);
        if (tip.submissionSubStatusObj) {
          tip.submissionStatusStr += "(" + $filter("translate")(tip.submissionStatusObj.label) + ")";
        }
      },

      openUrl: function(url) {
        $window.open(url, "_blank");
      },

      print: function() {
        $window.print();
      },

      setHostname: function(hostname) {
        var req = {
          "operation": "set_hostname",
          "args": {
            "value": hostname
          }
        };

        return $http({method: "PUT", url: "admin/config", data: req});
      }
    };
}]).
  factory("fieldUtilities", ["$filter", "topojson", "CONSTANTS", function($filter, topojson, CONSTANTS) {
      var flatten_field = function(id_map, field) {
        if (field.children.length === 0) {
          id_map[field.id] = field;
          return id_map;
        } else {
          id_map[field.id] = field;
          return field.children.reduce(flatten_field, id_map);
        }
      };

      var prepare_field_answers_structure = function(field) {
        if (field.answers_structure === undefined) {
          field.answer_structure = {};
          if (field.type === "fieldgroup") {
            angular.forEach(field.children, function(child) {
              field.answer_structure[child.id] = [prepare_field_answers_structure(child)];
            });
          }
        }
        return field.answer_structure;
      };

      return {
        getValidator: function(field) {
          var validators = {
            "custom": field.attrs.regexp.value,
            "none": "",
            "email": CONSTANTS.email_regexp,
            "number": CONSTANTS.number_regexp,
            "phonenumber": CONSTANTS.phonenumber_regexp,
          };

          return validators[field.attrs.input_validation.value];
        },

        minY: function(arr) {
          return $filter("min")($filter("map")(arr, "y"));
        },

        splitRows: function(fields) {
          var rows = [];
          var y = null;

          angular.forEach(fields, function(f) {
            if(y !== f["y"]) {
              y = f["y"];
              rows.push([]);
            }

            rows[rows.length - 1].push(f);
          });

          return rows;
        },

        prepare_field_answers_structure: prepare_field_answers_structure,

        flatten_field: flatten_field,

        build_field_id_map: function(questionnaire) {
          return questionnaire.steps.reduce(function(id_map, cur_step) {
            return cur_step.children.reduce(flatten_field, id_map);
          }, {});
        },

        underscore: function(s) {
          return s.replace(new RegExp("-", "g"), "_");
        },

        stepFormName: function(id) {
          return "stepForm_" + this.underscore(id);
        },

        fieldFormName: function(id) {
          return "fieldForm_" + this.underscore(id);
        },

        findField: function(answers_obj, field_id) {
          var r;

          for (var key in answers_obj) {
            if (!key.match(CONSTANTS.uuid_regexp)) {
              continue;
            }

            if (key === field_id) {
              return answers_obj[key][0];
            }

            if (answers_obj.hasOwnProperty(key) && answers_obj[key] instanceof Array && answers_obj[key].length) {
              r = this.findField(answers_obj[key][0], field_id);
              if (r !== undefined) {
                return r;
              }
            }
          }
          return r;
        },

        isFieldTriggered: function(parent, field, answers, score) {
          var count = 0;
          var i;

          if (parent !== null && !parent.enabled) {
            field.enabled = false;
            return false;
          }

          if (field.triggered_by_score > score) {
            field.enabled = false;
            return false;
          }

          if (!field.triggered_by_options || field.triggered_by_options.length === 0) {
            field.enabled = true;
            return true;
          }

          for (i=0; i < field.triggered_by_options.length; i++) {
            var trigger = field.triggered_by_options[i];
            var answers_field = this.findField(answers, trigger.field);
            if (answers_field === undefined) {
              continue;
            }

            // Check if triggering field is in answers object
            if (trigger.option === answers_field.value ||
                (answers_field.hasOwnProperty(trigger.option) && answers_field[trigger.option])) {
              if (trigger.sufficient) {
                field.enabled = true;
                return true;
              }

              count += 1;
            }
          }

          if (count === field.triggered_by_options.length) {
              field.enabled = true;
              return true;
          }

          field.enabled = false;
          return false;
        },

        calculateScore: function(scope, field, entry) {
          var total_score, i;

          if (["selectbox", "multichoice"].indexOf(field.type) > -1) {
            for(i=0; i<field.options.length; i++) {
              if (entry["value"] === field.options[i].id) {
                if (field.options[i].score_type === 1) {
                  // Addition
                  scope.points_to_sum += field.options[i].score_points;
                } else if (field.options[i].score_type === 2) {
                  // Multiplication
                  scope.points_to_mul *= field.options[i].score_points;
                }
              }
            }
          } else if (field.type === "checkbox") {
            for(i=0; i<field.options.length; i++) {
              if (entry[field.options[i].id]) {
                if (field.options[i].score_type === 1) {
                  // Addition
                  scope.points_to_sum += field.options[i].score_points;
                } else if (field.options[i].score_type === 2) {
                  // Multiplication
                  scope.points_to_mul *= field.options[i].score_points;
                }
              }
            }
          }

          total_score = scope.points_to_sum * scope.points_to_mul;

          if (total_score < scope.context.score_threshold_medium) {
            scope.total_score = 1;
          } else if (total_score < scope.context.score_threshold_high) {
            scope.total_score = 2;
          } else {
            scope.total_score = 3;
          }
        },

        updateAnswers: function(scope, parent, list, answers) {
          var entry, option, i, j;
          var self = this;

          angular.forEach(list, function(field) {
            if (self.isFieldTriggered(parent, field, scope.answers, scope.total_score)) {
              field.enabled = true;
            } else {
              field.enabled = false;
              if (field.id in scope.answers) {
                scope.answers[field.id].splice(0, scope.answers[field.id].length);
                scope.answers[field.id].push(angular.copy(self.prepare_field_answers_structure(field)));
              }
            }

            angular.forEach(list, function(field) {
              for (i=0; i<answers[field.id].length; i++) {
                self.updateAnswers(scope, field, field.children, answers[field.id][i]);
              }
            });

            if (!field.enabled) {
              return;
            }

            if (scope.node.enable_scoring_system) {
              angular.forEach(scope.answers[field.id], function(entry) {
                self.calculateScore(scope, field, entry);
              });
            }

            for(i=0; i<answers[field.id].length; i++) {
              entry = answers[field.id][i];

              /* Block related to updating required status */
              if (["inputbox", "textarea"].indexOf(field.type) > -1) {
                entry.required_status = (field.required || field.attrs.min_len.value > 0) && !entry["value"];
              } else if (field.type === "checkbox") {
                if (!field.required) {
                  entry.required_status = false;
                } else {
                  entry.required_status = true;
                  for (j=0; j<field.options.length; j++) {
                    if (entry[field.options[j].id]) {
                      entry.required_status = false;
                      break;
                    }
                  }
                }
              } else {
                entry.required_status = field.required && !entry["value"];
              }

              /* Block related to evaluate options */
              if (["checkbox", "selectbox", "multichoice"].indexOf(field.type) > -1) {
                for (j=0; j<field.options.length; j++) {
                  option = field.options[j];
                  option.set = false;
                  if(field.type === "checkbox") {
                    if(entry[option.id]) {
                      option.set = true;
                    }
                  } else {
                    if (option.id === entry["value"]) {
                      option.set = true;
                    }
                  }

                  if (option.set) {
                    if (option.block_submission) {
                      scope.block_submission = true;
                    }

                    if (option.trigger_receiver.length) {
                      scope.replaceReceivers(option.trigger_receiver);
                    }
                  }
                }
              }
            }
          });
        },

        onAnswersUpdate: function(scope) {
          var self = this;
          scope.block_submission = false;
          scope.total_score = 0;
          scope.points_to_sum = 0;
          scope.points_to_mul = 1;

          if(!scope.questionnaire) {
            return;
          }

          scope.submission.setContextReceivers(scope.context.id);

          angular.forEach(scope.questionnaire.steps, function(step) {
            if (self.isFieldTriggered(null, step, scope.answers, scope.total_score)) {
              step.enabled = true;
            } else {
              step.enabled = false;
            }

            self.updateAnswers(scope, step, step.children, scope.answers);
          });

          if (scope.submission) {
            scope.submission._submission.total_score = scope.total_score;
            scope.submission.blocked = scope.block_submission;
          }
        },

        parseField: function(field, parsedFields) {
          var self = this;
          if (!field.editable) {
            return;
          }

          if (!Object.keys(parsedFields).length) {
            parsedFields.fields = [];
            parsedFields.fields_by_id = {};
            parsedFields.options_by_id = {};
          }

          if (["checkbox", "selectbox", "multichoice"].indexOf(field.type) > -1) {
            parsedFields.fields_by_id[field.id] = field;
            parsedFields.fields.push(field);
            field.options.forEach(function(option) {
              parsedFields.options_by_id[option.id] = option;
            });

          } else if (field.type === "fieldgroup") {
            field.children.forEach(function(field) {
              self.parseField(field, parsedFields);
            });
          } else if (field.type === "map") {
            d3.json(field.attrs.topojson.value).then(function(topojson) {
             field.attrs.topojson.geojson = self.topoToGeo(topojson);
             field.attrs.topojson.id_name_map = {};
             field.attrs.topojson.geojson.features.forEach(function(feature) {
               field.attrs.topojson.id_name_map[feature.id] = feature.properties.name;
             });
            });
          }
        },

        parseFields: function(fields) {
          var self = this;
          var parsedFields = {};

          fields.forEach(function(field) {
            self.parseField(field, parsedFields);
          });

          return parsedFields;
        },

        parseQuestionnaire: function(questionnaire) {
          var self = this;
          var parsedFields = {};

          questionnaire.steps.forEach(function(step) {
            parsedFields = self.parseFields(step.children, parsedFields);
          });

          return parsedFields;
        },

        topoToGeo: function(data) {
          return topojson.feature(data, data.objects[Object.keys(data.objects)[0]]);
        }
      };
}]).
  constant("CONSTANTS", {
     /* The email regexp restricts email addresses to less than 400 chars. See #1215 */
     "email_regexp": /^([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}[\w]{1,100}$/,
     "number_regexp": /^\d+$/,
     "phonenumber_regexp": /^[+]?[ \d]+$/,
     "hostname_regexp": /^[a-z0-9-.]+$|^$/,
     "onionservice_regexp": /^[0-9a-z]{16}\.onion$/,
     "https_regexp": /^https:\/\/([a-z0-9-]+)\.(.*)$|^$/,
     "uuid_regexp": /^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/
}).
  factory("GLTranslate", ["$translate", "$location","tmhDynamicLocale",
  function($translate, $location, tmhDynamicLocale) {

  // facts are (un)defined in order of importance to the factory.
  var facts = {
    userChoice: undefined,
    urlParam: undefined,
    userPreference: undefined,
    browserSniff: undefined,
    nodeDefault: undefined
  };

  // This is a value set by the node.
  var enabledLanguages = [];

  // Country codes with multiple languages or an '_XX' extension
  var problemLangs = {
    "zh": ["CN", "TW"],
    "pt": ["BR", "PT"],
    "nb": "NO",
    "hr": "HR",
    "hu": "HU",
  };

  var state = {
    language: null
  };

  initializeStartLanguage();

  function initializeStartLanguage() {
    var queryLang = $location.search().lang;
    if (angular.isDefined(queryLang) && validLang(queryLang)) {
      facts.urlParam = queryLang;
    }

    var s = normalizeLang(window.navigator.language);
    if (validLang(s)) {
      facts.browserSniff = s;
    }

    determineLanguage();
  }

  // normalizeLang attempts to map input language strings to the transifex format.
  function normalizeLang(s) {
    if (typeof s !== "string") {
      return "";
    }

    if (s.length !== 2 && s.length !== 5) {
      // The string is not in a format we are expecting so just return it.
      return s;
    }

    // The string is probably a valid ISO 639-1 language.
    var iso_lang = s.slice(0,2).toLowerCase();

    if (problemLangs.hasOwnProperty(iso_lang)) {

      var t = problemLangs[iso_lang];
      if (t instanceof Array) {
        // We do not know which extension to use, so just use the most popular one.
        return iso_lang + "_" + t[0];
      }
      return iso_lang + "_" + t;

    } else {
      return iso_lang;
    }
  }

  function validLang(inp) {
    if (typeof inp !== "string") {
      return false;
    }

    // Check if lang is in the list of enabled langs if we have enabledLangs
    if (enabledLanguages.length > 0) {
      return enabledLanguages.indexOf(inp) > -1;
    }

    return true;
  }

  // TODO updateTranslationServices should return a promise.
  function updateTranslationServices(lang) {
    // Set text direction for languages that read from right to left.
    var useRightToLeft = ["ar", "fa", "he", "ur"].indexOf(lang) !== -1;
    document.getElementsByTagName("html")[0].setAttribute("dir", useRightToLeft ? "rtl" : "ltr");

    // Update the $translate module to use the new language.
    $translate.use(lang).then(function() {
      // TODO reload the new translations returned by node.
    });

    // For languages that are of the form 'zh_TW', handle the mapping of 'lang'
    // to angular-i18n locale name as best we can. For example: 'zh_TW' becomes 'zh-tw'
    var t = lang;
    if (lang.length === 5) {
      // Angular-i18n's format is typically 'zh-tw'
      t = lang.replace("_", "-").toLowerCase();
    }

    tmhDynamicLocale.set(t);
  }


  // setLang either uses the current state.language or the passed value
  // to set the language for the entire application.
  function setLang(choice) {
    if (angular.isUndefined(choice)) {
      choice = state.language;
    }

    if (validLang(choice)) {
      facts.userChoice = choice;
      determineLanguage();
    }
  }

  function isSelectable(language) {
    if (!angular.isDefined(language)) {
        return false;
    }
    if (enabledLanguages.length > 0) {
        return enabledLanguages.indexOf(language) !== -1;
    }

    return true;
  }

  // bestLanguage returns the best language for the application to use given
  // all of the state the GLTranslate service has collected in facts. It picks
  // the language in the order that the properties of the 'facts' object is
  // defined.
  // { object -> string }
  function bestLanguage(facts) {
    if (isSelectable(facts.userChoice)) {
      return facts.userChoice;
    } else if (isSelectable(facts.urlParam)) {
      return facts.urlParam;
    } else if (isSelectable(facts.userPreference)) {
      return facts.userPreference;
    } else if (isSelectable(facts.browserSniff)) {
      return facts.browserSniff;
    } else if (isSelectable(facts.nodeDefault)) {
      return facts.nodeDefault;
    } else {
      return null;
    }
  }

  // determineLanguage contains all of the scope creeping ugliness of the
  // factory. It finds the best language to use, changes the language
  // pointer, and notifies the dependent services of the change.
  function determineLanguage() {
    state.language = bestLanguage(facts);
    if (state.language !== null) {
      updateTranslationServices(state.language);
      GLClient.language = state.language;
    }
  }

  return {
    // Use state object to preserve the reference to language across scopes.
    state: state,

    setLang: setLang,

    addNodeFacts: function(defaultLang, languages_enabled) {
      facts.nodeDefault = defaultLang;

      enabledLanguages = languages_enabled;

      determineLanguage();
    },

    addUserPreference: function(lang) {
      facts.userPreference = lang;
      determineLanguage();
    },
  };
}]);
