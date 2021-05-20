GL.factory("GLResource", ["$resource", function($resource) {
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
  ["$filter", "$http", "$location", "$window", "$routeParams", "$rootScope", "GLTranslate", "UserPreferences", "TokenResource",
  function($filter, $http, $location, $window, $routeParams, $rootScope, GLTranslate, UserPreferences, TokenResource) {
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
          "two_factor": response.two_factor,
          "management_session": response.management_session,
          "homepage": "",
          "preferencespage": ""
        };

        function initPreferences(prefs) {
          $rootScope.preferences = prefs;
          GLTranslate.addUserPreference(prefs.language);
        }

        if (self.session.role !== "whistleblower") {
          var role = self.session.role === "receiver" ? "recipient" : self.session.role;

          self.session.homepage = "/" + role + "/home";
          self.session.preferencespage = "/" + role + "/preferences";

          UserPreferences.get().$promise.then(initPreferences);
        }

        self.session.role_l10n = function() {
          var ret = self.session.role === "receiver" ? "recipient" : self.session.role;
          return $filter("translate")(ret.charAt(0).toUpperCase() + ret.substr(1));
        };
      };

      self.login = function(tid, username, password, authcode, authtoken) {
        if (typeof authcode === "undefined") {
          authcode = "";
        }

        self.loginInProgress = true;

        var success_fn = function(response) {
          // reset login status before returning
          self.loginInProgress = false;

          if ("redirect" in response.data) {
            $window.location.replace(response.data.redirect);
          }

          self.set_session(response);

          if ($routeParams.src) {
            $location.path($routeParams.src);
          } else {
            // Override the auth_landing_page if a password change is needed
            if (self.session.role === "whistleblower") {
              $rootScope.setPage("tippage");
            } else {
              $location.path(self.session.homepage);
            }
          }

          $location.search("");
        };

        return new TokenResource().$get().then(function(token) {
          if (authtoken) {
            return $http.post("api/tokenauth?token=" + token.id, {"authtoken": authtoken}).
              then(success_fn, function() {
                self.loginInProgress = false;
              });
          } else {
            if (username === "whistleblower") {
              password = password.replace(/\D/g,"");
              return $http.post("api/receiptauth?token=" + token.id, {"receipt": password}).
                then(success_fn, function() {
                  self.loginInProgress = false;
                });
            } else {
            return $http.post("api/authentication?token=" + token.id, {"tid": tid, "username": username, "password": password, "authcode": authcode}).
              then(success_fn, function() {
                self.loginInProgress = false;
              });
            }
          }
        });
      };

      self.deleteSession = function() {
        if (self.session) {
          self.session = undefined;
        }
      };

      self.logout = function() {
        var cb;

        $rootScope.Authentication.authcoderequired = false;

        if (self.session.role === "whistleblower") {
          cb = function() {
            self.deleteSession();
            $rootScope.setPage("homepage");
          };
        } else {
          cb = function() {
            self.deleteSession();
            self.loginRedirect(true);
          };
        }

        return $http.delete("api/session").then(cb, cb);
      };

      self.loginRedirect = function(isLogout) {
        var source_path = $location.path();

        if (source_path !== "/login") {
          $location.path("/login");
          if (!isLogout) {
            $location.search("src=" + source_path);
          }
        }
      };

      self.hasUserRole = function() {
        if (angular.isUndefined(self.session)) {
          return false;
        }

        return ["admin", "receiver", "custodian"].indexOf(self.session.role) !== -1;
      };

      self.get_headers = function() {
        var h = {};

        if (self.session) {
          h["X-Session"] = self.session.id;
        }

        h["Accept-Language"] = GLTranslate.state.language;

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
      if (typeof Authentication.session === "undefined") {
        return $q.resolve(Access.OK);
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    },

    isAuthenticated: function (role) {
      if (Authentication.session && (role === "*" || Authentication.session.role === role)) {
        return $q.resolve(Access.OK);
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    }
  };

  return Access;
}]).
factory("PublicResource", ["GLResource", function(GLResource) {
  return new GLResource("api/public");
}]).
factory("TokenResource", ["GLResource", "glbcProofOfWork", function(GLResource, glbcProofOfWork) {
  return new GLResource("api/token/:id", {id: "@id"}, {
    get: {
      method: "post",
      interceptor: {
        response: function(response) {
          var token = response.resource;
          return glbcProofOfWork.proofOfWork(token.id).then(function(result) {
            token.answer = result;
            return token.$update().then(function(token) {
              return token;
            });
          });
        }
      }
    }
  });
}]).
factory("SubmissionResource", ["GLResource", function(GLResource) {
  return new GLResource("api/submission/:id?token=:token_id", {id: "@id", token_id: "@token_id"});
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
factory("Submission", ["$q", "GLResource", "$filter", "$location", "$rootScope", "SubmissionResource", "TokenResource",
    function($q, GLResource, $filter, $location, $rootScope, SubmissionResource, TokenResource) {

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
    self.mandatory_receivers = 0;
    self.optional_receivers = 0;
    self.selected_receivers = {};
    self.done = false;

    self.setContextReceivers = function(context_id) {
      self.context = $rootScope.contexts_by_id[context_id];

      // bypass the re-initialization if recipients are manually selected
      if (Object.keys(self.selected_receivers).length && self.context.allow_recipients_selection) {
        return;
      }

      self.selected_receivers = {};
      self.receivers = [];

      angular.forEach(self.context.receivers, function(receiver) {
        var r = $rootScope.receivers_by_id[receiver];
        self.receivers.push(r);

        if (r.forcefully_selected) {
          self.mandatory_receivers += 1;
        } else {
          self.optional_receivers += 1;
        }

        if ((self.context.select_all_receivers) || r.forcefully_selected) {
          self.selected_receivers[r.id] = true;
        }
      });
    };

    self.countSelectedReceivers = function() {
      return Object.keys(self.selected_receivers).length;
    };

    /**
     * @name Submission.create
     * @description
     * Create a new submission based on the currently selected context.
     *
     * */
    self.create = function(context_id) {
      self.setContextReceivers(context_id);

      self._submission = new SubmissionResource({
        id: null,
        context_id: self.context.id,
        receivers: [],
        identity_provided: false,
        answers: {},
        answer: 0,
        total_score: 0,
        removed_files: []
      });

      new TokenResource().$get().then(function(token) {
        new SubmissionResource().$get({'token_id': token.id}).then(function(ret) {
          self.id = ret.id;
	  self._submission.id = ret.id;
	});
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

      return new TokenResource().$get().then(function(token) {
        return self._submission.$update({'token_id': token.id}).then(function(result) {
          if (result) {
            $rootScope.receipt = self._submission.receipt;
            $rootScope.setPage("receiptpage");
          }
        });
      });
    };

    fn(self);
  };
}]).
factory("RTipResource", ["GLResource", function(GLResource) {
  return new GLResource("api/rtips/:id", {id: "@id"});
}]).
factory("RTipCommentResource", ["GLResource", function(GLResource) {
  return new GLResource("api/rtips/:id/comments", {id: "@id"});
}]).
factory("RTipMessageResource", ["GLResource", function(GLResource) {
  return new GLResource("api/rtips/:id/messages", {id: "@id"});
}]).
factory("RTipIdentityAccessRequestResource", ["GLResource", function(GLResource) {
  return new GLResource("api/rtips/:id/iars", {id: "@id"});
}]).
factory("RTipDownloadRFile", ["$http", "$window", "TokenResource", function($http, $window, TokenResource) {
  return function(file) {
    return new TokenResource().$get().then(function(token) {
      $window.open("api/rfile/" + file.id + "?token=" + token.id);
    });
  };
}]).
factory("RTipWBFileResource", ["GLResource", function(GLResource) {
  return new GLResource("api/wbfile/:id", {id: "@id"});
}]).
factory("RTipDownloadWBFile", ["$http", "$window", "TokenResource", function($http, $window, TokenResource) {
  return function(file) {
    return new TokenResource().$get().then(function(token) {
      $window.open("api/wbfile/" + file.id + "?token=" + token.id);
    });
  };
}]).
factory("RTipExport", ["$http", "$window", "TokenResource", function($http, $window, TokenResource) {
  return function(tip) {
    return new TokenResource().$get().then(function(token) {
      $window.open("api/rtips/" + tip.id + "/export?token=" + token.id);
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
      tip.last_iar = tip.iars.length ? tip.iars[tip.iars.length - 1] : null;

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

        return $http({method: "PUT", url: "api/rtips/" + tip.id, data: req});
      };

      tip.updateLabel = function(label) {
        return tip.operation("update_label", {"value": label}).then(function () {
          $rootScope.reload();
        });
      };

      tip.updateSubmissionStatus = function() {
        return tip.operation("update_status", {"status": tip.status, "substatus": tip.substatus ? tip.substatus : ""}).then(function () {
          $rootScope.reload();
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
  return new GLResource("api/wbtip");
}]).
factory("WBTipCommentResource", ["GLResource", function(GLResource) {
  return new GLResource("api/wbtip/comments");
}]).
factory("WBTipMessageResource", ["GLResource", function(GLResource) {
  return new GLResource("api/wbtip/messages/:id", {id: "@id"});
}]).
factory("WBTipDownloadFile", ["$http", "$window", "TokenResource", function($http, $window, TokenResource) {
  return function(file) {
    return new TokenResource().$get().then(function(token) {
      $window.open("api/wbtip/wbfile/" + file.id + "?token=" + token.id);
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
factory("ReceiverTips", ["GLResource", function(GLResource) {
  return new GLResource("api/rtips");
}]).
factory("IdentityAccessRequests", ["GLResource", function(GLResource) {
  return new GLResource("api/custodian/iars");
}]).
factory("AdminAuditLogResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/auditlog");
}]).
factory("AdminContextResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/contexts/:id", {id: "@id"});
}]).
factory("AdminQuestionnaireResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/questionnaires/:id", {id: "@id"});
}]).
factory("AdminStepResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/steps/:id", {id: "@id"});
}]).
factory("AdminFieldResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/fields/:id",{id: "@id"});
}]).
factory("AdminFieldTemplateResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/fieldtemplates/:id", {id: "@id"});
}]).
factory("AdminRedirectResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/redirects/:id", {id: "@id"});
}]).
factory("AdminTenantResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/tenants/:id", {id: "@id"});
}]).
factory("AdminUserResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/users/:id", {id: "@id"});
}]).
factory("AdminSubmissionStatusResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/submission_statuses/:id", {id: "@id"});
}]).
factory("AdminSubmissionSubStatusResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/submission_statuses/:submissionstatus_id/substatuses/:id", {id: "@id", submissionstatus_id: "@submissionstatus_id"});
}]).
factory("AdminNodeResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/node");
}]).
factory("AdminNotificationResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/notification");
}]).
factory("AdminL10NResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/l10n/:lang", {lang: "@lang"});
}]).
factory("AdminTLSConfigResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/config/tls", {}, {
    "enable":  { method: "POST", params: {}},
    "disable": { method: "PUT", params: {}},
  });
}]).
factory("AdminTLSCertFileResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/config/tls/files");
}]).
factory("AdminAcmeResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/config/acme/run");
}]).
factory("AdminTLSCfgFileResource", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/config/tls/files/:name", {name: "@name"});
}]).
factory("AdminUtils", ["AdminContextResource", "AdminQuestionnaireResource", "AdminStepResource", "AdminFieldResource", "AdminFieldTemplateResource", "AdminUserResource", "AdminNodeResource", "AdminNotificationResource", "AdminRedirectResource", "AdminTenantResource",
    function(AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminNodeResource, AdminNotificationResource, AdminRedirectResource, AdminTenantResource) {
  return {
    new_context: function() {
      var context = new AdminContextResource();
      context.id = "";
      context.status = "hidden";
      context.name = "";
      context.description = "";
      context.languages = "",
      context.order = 0;
      context.tip_timetolive = 90;
      context.show_recipients_details = false;
      context.allow_recipients_selection = false;
      context.show_receivers_in_alphabetical_order = true;
      context.show_steps_navigation_interface = true;
      context.select_all_receivers = true;
      context.maximum_selectable_receivers = 0;
      context.enable_comments = true;
      context.enable_messages = false;
      context.enable_two_way_comments = true;
      context.enable_two_way_messages = true;
      context.enable_attachments = true;
      context.enable_rc_to_wb_files = false;
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
      return questionnaire;
    },

    new_step: function(questionnaire_id) {
      var step = new AdminStepResource();
      step.id = "";
      step.label = "";
      step.description = "";
      step.order = 0;
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
      field.descriptor_id = "";
      field.label = "";
      field.type = "inputbox";
      field.description = "";
      field.hint = "";
      field.placeholder = "";
      field.multi_entry = false;
      field.required = false;
      field.preview = false;
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
      field.instance = "template";
      field.label = "";
      field.type = "inputbox";
      field.description = "";
      field.placeholder = "";
      field.hint = "";
      field.multi_entry = false;
      field.required = false;
      field.preview = false;
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
      user.public_name = "";
      user.mail_address = "";
      user.pgp_key_fingerprint = "";
      user.pgp_key_remove = false;
      user.pgp_key_public = "";
      user.pgp_key_expiration = "";
      user.language = "en";
      user.notification = true;
      user.forcefully_selected = false;
      user.can_edit_general_settings = false;
      user.can_delete_submission = false;
      user.can_postpone_expiration = false;
      user.send_account_activation_link = true;
      return user;
    },

    new_redirect: function () {
      return new AdminRedirectResource();
    },

    new_tenant: function() {
      var tenant = new AdminTenantResource();
      tenant.active = true;
      tenant.name = "";
      tenant.mode = "default";
      tenant.subdomain = "";
      return tenant;
    }
  };
}]).
factory("UserPreferences", ["GLResource", function(GLResource) {
  return new GLResource("api/preferences", {}, {"update": {method: "PUT"}});
}]).
factory("TipsCollection", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/auditlog/tips");
}]).
factory("JobsAuditLog", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/auditlog/jobs");
}]).
factory("Files", ["GLResource", function(GLResource) {
  return new GLResource("api/admin/files");
}]).
factory("DefaultL10NResource", ["GLResource", function(GLResource) {
  return new GLResource("/data/l10n/:lang.json", {lang: "@lang"});
}]).
factory("Utils", ["$rootScope", "$http", "$q", "$location", "$filter", "$uibModal", "$window", "FileSaver",
    function($rootScope, $http, $q, $location, $filter, $uibModal, $window, FileSaver) {
  return {
    array_to_map: function(array) {
      var ret = {};
      angular.forEach(array, function(element) {
        ret[element.id] = element;
      });
      return ret;
    },

    set_title: function() {
      if (!$rootScope.public) {
        return;
      }

      var pt1 = $rootScope.public.node.name,
          pt2 = $rootScope.public.node.header_title_homepage;

      if ($location.path() === "/") {
        if ($rootScope.page === "tippage") {
          pt2 = "Report";
        } else if ($rootScope.page === "signuppage") {
          pt2 = "Create your whistleblowing platform";
        }
      } else {
        pt2 = $rootScope.header_title;
      }

      pt2 = $filter("translate")(pt2);

      $rootScope.projectTitle = pt1;
      $rootScope.pageTitle = pt2;

      if (pt1 && pt2) {
        $rootScope.pt = pt1 + " - " + pt2;
      } else if (pt1) {
        $rootScope.pt = pt1;
      } else if (pt2) {
        $rootScope.pt = pt2;
      } else {
        $rootScope.pt = "GlobaLeaks";
      }

      $window.document.title = $rootScope.pt;
      $window.document.getElementsByName("description")[0].content = $rootScope.public.node.description;
    },

    route_check: function() {
      var path = $location.path();
      if (path !== "/") {
        $rootScope.page = "";
      }

      if (!$rootScope.public) {
        return;
      }

      if (!$rootScope.public.node.wizard_done) {
        $location.path("/wizard");
      } else if (path === "/" && $rootScope.public.node.enable_signup) {
        $rootScope.setPage("signuppage");
      } else if (["/", "/submission"].indexOf(path !== -1) && $rootScope.public.node.adminonly && !$rootScope.Authentication.session) {
        $location.path("/admin");
      } else if ($rootScope.Authentication.session && $rootScope.Authentication.session.role !== "whistleblower") {
        if ($rootScope.Authentication.session.password_change_needed) {
          $location.path("/actions/forcedpasswordchange");
        } else if ($rootScope.public.node.two_factor && !$rootScope.Authentication.session.two_factor) {
          $location.path("/actions/forcedtwofactor");
        }
      }
    },

    getXOrderProperty: function() {
      return "x";
    },

    getYOrderProperty: function(elem) {
      var key = "order";
      if (typeof elem[key] === "undefined") {
        key = "y";
      }
      return key;
    },

    null_function: function() {
      return true;
    },

    getCardSize: function(num) {
      if (num < 2) {
        return "col-md-12";
      } else if (num === 2) {
        return "col-md-6";
      } else if (num === 3) {
        return "col-md-4";
      } else {
        return "col-md-3 col-sm-6";
      }
    },

    update: function (model, cb, errcb) {
      model.$update(
        function() {
          if (typeof cb !== "undefined") { cb(); }
        },
        function() {
          if (typeof errcb !== "undefined") { errcb(); }
        }
      );
    },

    go: function (path) {
      $location.path(path);
    },

    isWhistleblowerPage: function() {
      return ["/", "/submission"].indexOf($location.path()) !== -1;
    },

    getCSSFlags: function() {
      return {
        "public": this.isWhistleblowerPage(),
        "embedded": $window.self !== $window.top,
        "block-user-input": $rootScope.showLoadingPanel
      };
    },

    showUserStatusBox: function() {
      return $rootScope.public.node.wizard_done && angular.isDefined($rootScope.Authentication.session) && !$rootScope.Authentication.session.password_change_needed;
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
        if (uploads[key].files.length && uploads[key].progress() !== 1) {
          return true;
        }
      }

      return false;
    },

    openConfirmableModalDialog: function(template, arg, scope) {
      scope = !scope ? $rootScope : scope;

      var modal = $uibModal.open({
        templateUrl: template,
        controller: "ConfirmableModalCtrl",
        scope: scope,
        resolve: {
          arg: function () {
            return arg;
          },
          confirmFun: null,
          cancelFun: null
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

    displayErrorMsg: function(reason) {
      var error = {
        "message": "local-failure",
        "arguments": [reason],
        "code": 10,
      };
      $rootScope.errors.push(error);
    },

    getSubmissionStatusText: function(status, substatus, submission_statuses) {
      var text;
      for (var i = 0; i < submission_statuses.length; i++) {
        if (submission_statuses[i].id === status) {
          text = $filter("translate")(submission_statuses[i].label);

          var substatuses = submission_statuses[i].substatuses;
          for (var j = 0; j < substatuses.length; j++) {
            if (substatuses[j].id === substatus) {
              text += "(" + $filter("translate")(substatuses[j].label) + ")";
              break;
            }
          }
          break;
        }
      }

      return text;
    },

    print: function() {
      $window.print();
    },

    scrollToTop: function() {
      $window.document.getElementsByTagName("body")[0].scrollIntoView();
    },

    download: function(filename, url) {
      return $http({
        method: "GET",
        url: url,
        responseType: "blob",
      }).then(function (response) {
        FileSaver.saveAs(response.data, filename);
      });
    },

    applyConfig: function(cmd, value, refresh) {
      var req = {
        "operation": cmd,
        "args": {
          "value": value
        }
      };

      return $http({method: "PUT", url: "api/admin/config", data: req}).then(function() { if (refresh) { $rootScope.reload(); }});
    },

    removeFile: function (submission, list, file) {
      if (typeof submission._submission.removed_files !== "undefined") {
        submission._submission.removed_files.push(String(file.uniqueIdentifier));
      }

      for (var i = list.length - 1; i >= 0; i--) {
        if (list[i] === file) {
          list.splice(i, 1);
          file.abort();
        }
      }
    }
  };
}]).
factory("fieldUtilities", ["$filter", "$http", "CONSTANTS", function($filter, $http, CONSTANTS) {
    var flatten_field = function(id_map, field) {
      if (field.children.length === 0) {
        id_map[field.id] = field;
        return id_map;
      } else {
        id_map[field.id] = field;
        return field.children.reduce(flatten_field, id_map);
      }
    };

    return {
      getClass: function(field, row_length) {
        if (field.width !== 0) {
          return "col-md-" + field.width;
        }

        return "col-md-" + ((row_length > 12) ? 1 : (12 / row_length));
      },

      getValidator: function(field) {
        var validators = {
          "custom": field.attrs.regexp ? field.attrs.regexp.value : "",
          "none": "",
          "email": CONSTANTS.email_regexp,
          "number": CONSTANTS.number_regexp,
          "phonenumber": CONSTANTS.phonenumber_regexp,
        };

        if (field.attrs.input_validation) {
          return validators[field.attrs.input_validation.value];
        } else {
          return "";
        }
      },

      minY: function(arr) {
        return $filter("min")($filter("map")(arr, "y"));
      },

      splitRows: function(fields) {
        var rows = [];
        var y = null;

        angular.forEach(fields, function(f) {
          if(y !== f.y) {
            y = f.y;
            rows.push([]);
          }

          rows[rows.length - 1].push(f);
        });

        return rows;
      },

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
            if (typeof r !== "undefined") {
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
          if (typeof answers_field === "undefined") {
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
        var self = this;
        var total_score, i;

        if (["selectbox", "multichoice"].indexOf(field.type) > -1) {
          for(i=0; i<field.options.length; i++) {
            if (entry["value"] === field.options[i].id) {
              if (field.options[i].score_type === "addition") {
                scope.points_to_sum += field.options[i].score_points;
              } else if (field.options[i].score_type === "multiplier") {
                scope.points_to_mul *= field.options[i].score_points;
              }
            }
          }
        } else if (field.type === "checkbox") {
          for(i=0; i<field.options.length; i++) {
            if (entry[field.options[i].id]) {
              if (field.options[i].score_type === "addition") {
                scope.points_to_sum += field.options[i].score_points;
              } else if (field.options[i].score_type === "multiplier") {
                scope.points_to_mul *= field.options[i].score_points;
              }
            }
          }
        } else if (field.type === "fieldgroup") {
          angular.forEach(field.children, function(field) {
            angular.forEach(entry[field.id], function(entry) {
              self.calculateScore(scope, field, entry);
            });
          });

          return;
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
            if (!(field.id in answers)) {
              answers[field.id] = [{}];
            }
          } else {
            if (field.id in answers) {
              answers[field.id] = [{}];
            }
          }

          if (field.id in answers) {
            for (i=0; i<answers[field.id].length; i++) {
              self.updateAnswers(scope, field, field.children, answers[field.id][i]);
            }
          } else {
            self.updateAnswers(scope, field, field.children, {});
          }

          if (!field.enabled) {
            return;
          }

          if (scope.public.node.enable_scoring_system) {
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

        if (scope.context) {
          scope.submission.setContextReceivers(scope.context.id);
        }

        angular.forEach(scope.questionnaire.steps, function(step) {
          step.enabled = self.isFieldTriggered(null, step, scope.answers, scope.total_score);

          self.updateAnswers(scope, step, step.children, scope.answers);
        });

        if (scope.context) {
          scope.submission._submission.total_score = scope.total_score;
          scope.submission.blocked = scope.block_submission;
        }
      },

      parseField: function(field, parsedFields) {
        var self = this;

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
        }

        return parsedFields;
      },

      parseFields: function(fields, parsedFields) {
        var self = this;

        fields.forEach(function(field) {
          parsedFields = self.parseField(field, parsedFields);
        });

        return parsedFields;
      },

      parseQuestionnaire: function(questionnaire, parsedFields) {
        var self = this;

        questionnaire.steps.forEach(function(step) {
          parsedFields = self.parseFields(step.children, parsedFields);
        });

        return parsedFields;
      }
    };
}]).
factory("GLTranslate", ["$translate", "$location", "$window", "tmhDynamicLocale",
    function($translate, $location, $window, tmhDynamicLocale) {

  // facts are (un)defined in order of importance to the factory.
  var facts = {
    userChoice: null,
    urlParam: null,
    userPreference: null,
    nodeDefault: null
  };

  // This is a value set by the public.node.
  var enabledLanguages = [];

  var state = {
    language: null
  };

  initializeStartLanguage();

  function initializeStartLanguage() {
    var queryLang = $location.search().lang;
    if (angular.isDefined(queryLang) && validLang(queryLang)) {
      facts.urlParam = queryLang;
    }

    determineLanguage();
  }

  function validLang(inp) {
    if (typeof inp !== "string") {
      return false;
    }

    // Check if lang is in the list of enabled langs if we have enabledLangs
    if (enabledLanguages.length) {
      return enabledLanguages.indexOf(inp) > -1;
    }

    return true;
  }

  // TODO updateTranslationServices should return a promise.
  function updateTranslationServices(lang) {
    // Set text direction for languages that read from right to left.
    var useRightToLeft = ["ar", "dv", "fa", "he", "ur"].indexOf(lang) !== -1;
    document.getElementsByTagName("html")[0].setAttribute("dir", useRightToLeft ? "rtl" : "ltr");

    // Update the $translate module to use the new language.
    $translate.use(lang).then(function() {
      // TODO reload the new translations returned by public.node.
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
    if (language === null) {
        return false;
    }

    if (enabledLanguages.length) {
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
    var lang = "*";
    if (isSelectable(facts.userChoice)) {
      lang = facts.userChoice;
    } else if (isSelectable(facts.urlParam)) {
      lang = facts.urlParam;
    } else if (isSelectable(facts.userPreference)) {
      lang = facts.userPreference;
    } else if (isSelectable(facts.nodeDefault)) {
      lang = facts.nodeDefault;
    }

    return lang;
  }

  // determineLanguage contains all of the scope creeping ugliness of the
  // factory. It finds the best language to use, changes the language
  // pointer, and notifies the dependent services of the change.
  function determineLanguage() {
    GL.language = state.language = bestLanguage(facts);
    if (state.language !== "*") {
      updateTranslationServices(state.language);
      $window.document.getElementsByTagName("html")[0].setAttribute("lang", state.language);
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
