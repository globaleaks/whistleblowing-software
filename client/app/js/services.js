angular.module('GLServices', ['ngResource']).
  factory('GLResource', ['$resource', function($resource) {
    return function(url, params, actions) {
      var defaults = {
        get:    {method: 'get'},
        query:  {method: 'get', isArray: true},
        update: {method: 'put'}
      };

      actions = angular.extend(defaults, actions);

      return $resource(url, params, actions);
    };
  }]).
  factory('Authentication',
    ['$http', '$location', '$routeParams', '$rootScope', '$timeout', 'GLTranslate', 'locationForce', 'UserPreferences', 'ReceiverPreferences',
    function($http, $location, $routeParams, $rootScope, $timeout, GLTranslate, locationForce, UserPreferences, ReceiverPreferences) {
      function Session(){
        var self = this;

        self.loginInProgress = false;

        self.login = function(username, password, cb) {
          self.loginInProgress = true;

          var success_fn = function(response) {
            self.session = {
              'id': response.session_id,
              'user_id': response.user_id,
              'username': username,
              'role': response.role,
              'state': response.state,
              'password_change_needed': response.password_change_needed,
              'homepage': '',
              'auth_landing_page': ''
            };

            function initPreferences(prefs) {
              $rootScope.preferences = prefs;
              GLTranslate.addUserPreference(prefs.language);
            }

            if (self.session.role === 'admin') {
              self.session.homepage = '#/admin/landing';
              self.session.auth_landing_page = '/admin/landing';
              self.session.preferencespage = '#/user/preferences';
              UserPreferences.get().$promise.then(initPreferences);
            } else if (self.session.role === 'custodian') {
              self.session.homepage = '#/custodian/identityaccessrequests';
              self.session.auth_landing_page = '/custodian/identityaccessrequests';
              self.session.preferencespage = '#/user/preferences';
              UserPreferences.get().$promise.then(initPreferences);
            } else if (self.session.role === 'receiver') {
              self.session.homepage = '#/receiver/tips';
              self.session.auth_landing_page = '/receiver/tips';
              self.session.preferencespage = '#/receiver/preferences';
              ReceiverPreferences.get().$promise.then(initPreferences);
            } else if (self.session.role === 'whistleblower') {
              self.session.auth_landing_page = '/status';
            }

            // reset login state before returning
            self.loginInProgress = false;

            if (cb){
              return cb(response);
            }

            if ($routeParams.src) {
              $location.path($routeParams.src);
            } else {
              // Override the auth_landing_page if a password change is needed
              if (self.session.password_change_needed) {
                // Pushes ui to the ForcedPasswordChangeCtrl
                locationForce.set('/forcedpasswordchange');
              } else {
                $location.path(self.session.auth_landing_page);
              }
            }

            $location.search('');
          };

          if (username === 'whistleblower') {
            password = password.replace(/\D/g,'');
            return $http.post('receiptauth', {'receipt': password}).
            success(success_fn).
            error(function() {
              self.loginInProgress = false;
            });
          } else {
            return $http.post('authentication', {'username': username, 'password': password}).
            success(success_fn).
            error(function() {
              self.loginInProgress = false;
            });
          }
        };

        self.getLoginUri = function (role, path) {
          var loginUri = "/login";

          if (role === undefined ) {
            if (path === '/status') {
              loginUri = '/';
            } else if (path.indexOf('/admin') === 0) {
              loginUri = '/admin';
            } else if (path.indexOf('/custodian') === 0) {
              loginUri = '/custodian';
            }
          } else if (role === 'whistleblower') {
            loginUri = ('/');
          } else if (role === 'admin') {
            loginUri = '/admin';
          } else if (role === 'custodian') {
            loginUri = '/custodian';
          }

          return loginUri;
        };

        self.keycode = '';

        self.logout = function() {
          locationForce.clear();

          var logoutPerformed = function() {
            self.loginRedirect(true);
          };

          if (self.session.role === 'whistleblower') {
            $http.delete('receiptauth').then(logoutPerformed,
                                             logoutPerformed);
          } else {
            $http.delete('authentication').then(logoutPerformed,
                                                logoutPerformed);
          }
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
              $location.search('src=' + source_path);
            }
          }
        };

        self.hasUserRole = function() {
          if (angular.isUndefined(self.session)) {
            return false;
          }
          var r = self.session.role;
          return (r === 'admin' || r === 'receiver' || r === 'custodian');
        };

        self.get_headers = function() {
          var h = {};

          if (self.session) {
            h['X-Session'] = self.session.id;
          }

          if (GLTranslate.indirect.appLanguage !== null) {
            h['GL-Language'] = GLTranslate.indirect.appLanguage;
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
        return Access.OK;
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    },

    isAuthenticated: function (role) {
      if (Authentication.session && (role === '*' || Authentication.session.role === role)) {
        return Access.OK;
      } else {
        return $q.reject(Access.FORBIDDEN);
      }
    }
  };

  return Access;

}]).
  factory('globalInterceptor', ['$q', '$injector', '$window', '$rootScope',
  function($q, $injector, $window, $rootScope) {
    /* This interceptor is responsible for keeping track of the HTTP requests
     * that are sent and their result (error or not error) */

    return {
      request: function(config) {
        // A new request should display the loader overlay
        $rootScope.showLoadingPanel = true;
        return config;
      },

      response: function(response) {
        var $http = $injector.get('$http');

        // the last response should hide the loader overlay
        if ($http.pendingRequests.length < 1) {
          $rootScope.showLoadingPanel = false;
        }

        return response;
      },

      responseError: function(response) {
        /*
           When the response has failed write the rootScope
           errors array the error message.
        */
        var $http = $injector.get('$http');
        var Authentication = $injector.get('Authentication');

        if (response.status === 405) {
          var errorData = angular.toJson({
              errorUrl: $window.location.href,
              errorMessage: response.statusText,
              stackTrace: [{
                'url': response.config.url,
                'method': response.config.method
              }],
              agent: navigator.userAgent
            });

          $http.post('exception', errorData);
        }

        try {
          if (response.data !== null) {
            var error = {
              'message': response.data.error_message,
              'code': response.data.error_code,
              'arguments': response.data.arguments
            };

            /* 30: Not Authenticated */
            if (error.code === 30) {
              Authentication.loginRedirect(false);
            }

            $rootScope.errors.push(error);
          }
        } finally {
          if ($http.pendingRequests.length < 1) {
            $rootScope.showLoadingPanel = false;
          }
        }

        return $q.reject(response);
      }
    };
}]).
  factory('PublicResource', ['GLResource', function(GLResource) {
    return new GLResource('public');
}]).
  factory('TokenResource', ['GLResource', function(GLResource) {
    return new GLResource('token/:id', {id: '@id'});
}]).
  factory('SubmissionResource', ['GLResource', function(GLResource) {
    return new GLResource('submission/:id', {id: '@token_id'});
}]).
  factory('FieldAttrs', ['$resource', function($resource) {
    return $resource('data/field_attrs.json');
}]).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', ['$q', 'GLResource', '$filter', '$location', '$rootScope', 'Authentication', 'TokenResource', 'SubmissionResource',
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
      self.receivers_selected = {};
      self.done = false;

      self.isDisabled = function() {
        return (self.count_selected_receivers() === 0 ||
                self.wait ||
                !self.pow ||
                self.done);
      };

      self.count_selected_receivers = function () {
        var count = 0;

        angular.forEach(self.receivers_selected, function (selected) {
          if (selected) {
            count += 1;
          }
        });

        return count;
      };

      var setCurrentContextReceivers = function(context_id, receivers_ids) {
        self.context = angular.copy($filter('filter')($rootScope.contexts, {"id": context_id})[0]);

        self.receivers_selected = {};
        self.receivers = [];
        angular.forEach($rootScope.receivers, function(receiver) {
          if (self.context.receivers.indexOf(receiver.id) !== -1) {
            self.receivers.push(receiver);

            self.receivers_selected[receiver.id] = false;

            if (receivers_ids.length) {
              if (receivers_ids.indexOf(receiver.id) !== -1) {
                if ((receiver.pgp_key_public !== '' || $rootScope.node.allow_unencrypted) ||
                    receiver.configuration !== 'unselectable') {
                  self.receivers_selected[receiver.id] = true;
                }
              }
            } else {
              if (receiver.pgp_key_public !== '' || $rootScope.node.allow_unencrypted) {
                if (receiver.configuration === 'default') {
                  self.receivers_selected[receiver.id] = self.context.select_all_receivers;
                } else if (receiver.configuration === 'forcefully_selected') {
                  self.receivers_selected[receiver.id] = true;
                }
              }
            }
          }
        });

        // temporary fix for contitions in which receiver selection step is disabled but
        // select_all_receivers is marked false and the admin has forgotten to mark at least
        // one receiver to automtically selected nor the user is coming from a link with
        // explicit receivers selection.
        // in all this conditions we select all receivers for which submission is allowed.
        if (!self.context.allow_recipients_selection) {
          if (self.count_selected_receivers() === 0 && !self.context.select_all_receivers) {
            angular.forEach($rootScope.receivers, function(receiver) {
              if (self.context.receivers.indexOf(receiver.id) !== -1) {
                if (receiver.pgp_key_public !== '' || $rootScope.node.allow_unencrypted) {
                  if (receiver.configuration !== 'unselectable') {
                    self.receivers_selected[receiver.id] = true;
                  }
                }
              }
            });
          }
        }
      };

      /**
       * @name Submission.create
       * @description
       * Create a new submission based on the currently selected context.
       *
       * */
      self.create = function(context_id, receivers_ids, cb) {
        setCurrentContextReceivers(context_id, receivers_ids);

        self._submission = new SubmissionResource({
          context_id: self.context.id,
          receivers: [],
          identity_provided: false,
          answers: {},
          human_captcha_answer: 0,
          proof_of_work_answer: 0,
          graph_captcha_answer: "",
          total_score: 0
        });

        self._token = new TokenResource({'type': 'submission'}).$save(function(token) {
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
        if (!self._submission || !self.receivers_selected) {
          return;
        }

        self.done = true;

        self._submission.receivers = [];
        angular.forEach(self.receivers_selected, function(selected, id){
          if (selected) {
            self._submission.receivers.push(id);
          }
        });

        self._submission.$update(function(result){
          if (result) {
            Authentication.keycode = self._submission.receipt;
            $location.url("/receipt");
          }
        });

      };

      fn(self);
    };
}]).
  factory('RTipResource', ['GLResource', function(GLResource) {
    return new GLResource('rtip/:id', {id: '@id'});
}]).
  factory('RTipReceiverResource', ['GLResource', function(GLResource) {
    return new GLResource('rtip/:id/receivers', {id: '@id'});
}]).
  factory('RTipCommentResource', ['GLResource', function(GLResource) {
    return new GLResource('rtip/:id/comments', {id: '@id'});
}]).
  factory('RTipMessageResource', ['GLResource', function(GLResource) {
    return new GLResource('rtip/:id/messages', {id: '@id'});
}]).
  factory('RTipIdentityAccessRequestResource', ['GLResource', function(GLResource) {
    return new GLResource('rtip/:id/identityaccessrequests', {id: '@id'});
}]).
 factory('RTipDownloadFile', ['$http', '$filter', 'FileSaver', function($http, $filter, FileSaver) {
    return function(tip, file) {
      $http({
        method: 'GET',
        url: '/rtip/' + tip.id + '/download/' + file.id,
        responseType: 'blob',
      }).then(function (response) {
        var blob = response.data;
        FileSaver.saveAs(blob, file.name);
      });
    };
}]).
  factory('RTipExport', ['$http', '$filter', 'FileSaver', function($http, $filter, FileSaver) {
    return function(tip) {
      $http({
        method: 'GET',
        url: '/rtip/' + tip.id + '/export',
        responseType: 'blob',
      }).then(function (response) {
        var blob = response.data;
        var filename = $filter('tipFileName')(tip) + '.zip';
        FileSaver.saveAs(blob, filename);
      });
    };
}]).
  factory('RTip', ['$http', '$q', '$filter', 'RTipResource', 'RTipReceiverResource', 'RTipMessageResource', 'RTipCommentResource', 'RTipIdentityAccessRequestResource',
          function($http, $q, $filter, RTipResource, RTipReceiverResource, RTipMessageResource, RTipCommentResource, RTipIdentityAccessRequestResource) {
    return function(tipID, fn) {
      var self = this;

      self.tip = RTipResource.get(tipID, function (tip) {
        tip.receivers = RTipReceiverResource.query(tipID);
        tip.comments = tip.enable_comments ? RTipCommentResource.query(tipID) : [];
        tip.messages = tip.enable_messages ? RTipMessageResource.query(tipID) : [];
        tip.iars = tip.identity_provided ? RTipIdentityAccessRequestResource.query(tipID) : [];

        $q.all([tip.receivers.$promise, tip.comments.$promise, tip.messages.$promise, tip.iars.$promise]).then(function() {
          tip.iars = $filter('orderBy')(tip.iars, 'request_date');
          tip.last_iar = tip.iars.length > 0 ? tip.iars[tip.iars.length - 1] : null;

          tip.newComment = function(content) {
            var c = new RTipCommentResource(tipID);
            c.content = content;
            c.$save(function(newComment) {
              tip.comments.unshift(newComment);
            });
          };

          tip.newMessage = function(content) {
            var m = new RTipMessageResource(tipID);
            m.content = content;
            m.$save(function(newMessage) {
              tip.messages.unshift(newMessage);
            });
          };

          tip.setVar = function(var_name, var_value) {
            var req = {
              'operation': 'set',
              'args': {
                'key': var_name,
                'value': var_value
              }
            };

            return $http({method: 'PUT', url: '/rtip/' + tip.id, data: req}).success(function () {
              tip[var_name] = var_value;
            });
          };

          tip.updateLabel = function(label) {
            return tip.setVar('label', label);
          };

          if (fn) {
            fn(tip);
          }
        });
      });
    };
}]).
  factory('WBTipResource', ['GLResource', function(GLResource) {
    return new GLResource('wbtip');
}]).
  factory('WBTipReceiverResource', ['GLResource', function(GLResource) {
    return new GLResource('wbtip/receivers');
}]).
  factory('WBTipCommentResource', ['GLResource', function(GLResource) {
    return new GLResource('wbtip/comments');
}]).
  factory('WBTipMessageResource', ['GLResource', function(GLResource) {
    return new GLResource('wbtip/messages/:id', {id: '@id'});
}]).
  factory('WBTip', ['$q', '$rootScope', 'WBTipResource', 'WBTipReceiverResource', 'WBTipCommentResource', 'WBTipMessageResource',
      function($q, $rootScope, WBTipResource, WBTipReceiverResource, WBTipCommentResource, WBTipMessageResource) {
    return function(fn) {
      var self = this;

      self.tip = WBTipResource.get(function (tip) {
        tip.receivers = WBTipReceiverResource.query();
        tip.comments = tip.enable_comments ? WBTipCommentResource.query() : [];
        tip.messages = [];

        $q.all([tip.receivers.$promise, tip.comments.$promise]).then(function() {
          tip.msg_receiver_selected = null;
          tip.msg_receivers_selector = [];

          angular.forEach(tip.receivers, function(r1) {
            angular.forEach($rootScope.receivers, function(r2) {
              if (r2.id === r1.id) {
                tip.msg_receivers_selector.push({
                  key: r2.id,
                  value: r2.name
                });
              }
            });
          });

          tip.newComment = function(content) {
            var c = new WBTipCommentResource();
            c.content = content;
            c.$save(function(newComment) {
              tip.comments.unshift(newComment);
            });
          };

          tip.newMessage = function(content) {
            var m = new WBTipMessageResource({id: tip.msg_receiver_selected});
            m.content = content;
            m.$save(function(newMessage) {
              tip.messages.unshift(newMessage);
            });
          };

          tip.updateMessages = function () {
            if (tip.msg_receiver_selected) {
              WBTipMessageResource.query({id: tip.msg_receiver_selected}, function (messageCollection) {
                tip.messages = messageCollection;
              });
            }
          };

          if (fn) {
            fn(tip);
          }
        });
      });
    };
}]).
  factory('ReceiverPreferences', ['GLResource', function(GLResource) {
    return new GLResource('receiver/preferences');
}]).
  factory('ReceiverTips', ['GLResource', function(GLResource) {
    return new GLResource('receiver/tips');
}]).
  factory('IdentityAccessRequests', ['GLResource', function(GLResource) {
    return new GLResource('custodian/identityaccessrequests');
}]).
  factory('ReceiverOverview', ['GLResource', function(GLResource) {
    return new GLResource('admin/overview/users');
}]).
  factory('AdminContextResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/contexts/:id', {id: '@id'});
}]).
  factory('AdminQuestionnaireResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/questionnaires/:id', {id: '@id'});
}]).
  factory('AdminStepResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/steps/:id', {id: '@id'});
}]).
  factory('AdminFieldResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/fields/:id',{id: '@id'});
}]).
  factory('AdminFieldTemplateResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/fieldtemplates/:id', {id: '@id'});
}]).
  factory('AdminShorturlResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/shorturls/:id', {id: '@id'});
}]).
  factory('AdminUserResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/users/:id', {id: '@id'});
}]).
  factory('AdminReceiverResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/receivers/:id', {id: '@id'});
}]).
  factory('AdminNodeResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/node');
}]).
  factory('AdminNotificationResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/notification');
}]).
  factory('AdminL10NResource', ['GLResource', function(GLResource) {
    return new GLResource('admin/l10n/:lang', {lang: '@lang'});
}]).
  factory('AdminUtils', ['AdminContextResource', 'AdminQuestionnaireResource', 'AdminStepResource', 'AdminFieldResource', 'AdminFieldTemplateResource', 'AdminUserResource', 'AdminReceiverResource', 'AdminNodeResource', 'AdminNotificationResource', 'AdminShorturlResource',
    function(AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminReceiverResource, AdminNodeResource, AdminNotificationResource, AdminShorturlResource) {
  return {
    new_context: function() {
      var context = new AdminContextResource();
      context.id = '';
      context.name = '';
      context.description = '';
      context.presentation_order = 0;
      context.tip_timetolive = 15;
      context.show_context = true;
      context.show_recipients_details = false;
      context.allow_recipients_selection = false;
      context.show_receivers_in_alphabetical_order = true;
      context.select_all_receivers = true;
      context.maximum_selectable_receivers = 0;
      context.show_small_receiver_cards = false;
      context.enable_comments = true;
      context.enable_messages = false;
      context.enable_two_way_comments = true;
      context.enable_two_way_messages = true;
      context.enable_attachments = true;
      context.recipients_clarification = '';
      context.status_page_message = '';
      context.questionnaire_id = '';
      context.custodians = [];
      context.receivers = [];
      return context;
    },

    new_questionnaire: function() {
      var questionnaire = new AdminQuestionnaireResource();
      questionnaire.id = '';
      questionnaire.key = '';
      questionnaire.name = '';
      questionnaire.show_steps_navigation_bar = true;
      questionnaire.steps_navigation_requires_completion = true;
      questionnaire.steps = [];
      questionnaire.editable = true;
      return questionnaire;
    },

    new_step: function(questionnaire_id) {
      var step = new AdminStepResource();
      step.id = '';
      step.label = '';
      step.description = '';
      step.presentation_order = 0;
      step.children = [];
      step.questionnaire_id = questionnaire_id;
      step.triggered_by_score = 0;
      return step;
    },

    new_field: function(step_id, fieldgroup_id) {
      var field = new AdminFieldResource();
      field.id = '';
      field.key = '';
      field.instance = 'instance';
      field.editable = true;
      field.descriptor_id = '';
      field.label = '';
      field.type = 'inputbox';
      field.description = '';
      field.hint = '';
      field.multi_entry = false;
      field.multi_entry_hint = '';
      field.required = false;
      field.preview = false;
      field.stats_enabled = false;
      field.attrs = {};
      field.options = [];
      field.x = 0;
      field.y = 0;
      field.width = 0;
      field.children = [];
      field.fieldgroup_id = fieldgroup_id;
      field.step_id = step_id;
      field.template_id = '';
      field.triggered_by_score = 0;
      return field;
    },

    new_field_from_template: function(template_id, step_id, fieldgroup_id) {
      var field = this.new_field(step_id, fieldgroup_id);
      field.template_id = template_id;
      field.instance = 'reference';
      return field;
    },

    new_field_template: function (fieldgroup_id) {
      var field = new AdminFieldTemplateResource();
      field.id = '';
      field.key = '';
      field.instance = 'template';
      field.editable = true;
      field.label = '';
      field.type = 'inputbox';
      field.description = '';
      field.hint = '';
      field.multi_entry = false;
      field.multi_entry_hint = '';
      field.required = false;
      field.preview = false;
      field.stats_enabled = false;
      field.attrs = {};
      field.options = [];
      field.x = 0;
      field.y = 0;
      field.width = 0;
      field.children = [];
      field.fieldgroup_id = fieldgroup_id;
      field.step_id = '';
      field.template_id = '';
      field.triggered_by_score = 0;
      return field;
    },

    new_user: function () {
      var user = new AdminUserResource();
      user.id = '';
      user.username = '';
      user.role = 'receiver';
      user.state = 'enable';
      user.deletable = 'true';
      user.password = 'globaleaks';
      user.old_password = '';
      user.password_change_needed = true;
      user.state = 'enabled';
      user.name = '';
      user.description = '';
      user.public_name = '';
      user.mail_address = '';
      user.pgp_key_info = '';
      user.pgp_key_fingerprint = '';
      user.pgp_key_remove = false;
      user.pgp_key_public = '';
      user.pgp_key_expiration = '';
      user.language = 'en';
      return user;
    },

    new_shorturl: function () {
      return new AdminShorturlResource();
    }
  };
}]).
  factory('Admin', ['GLResource', '$q', 'AdminContextResource', 'AdminQuestionnaireResource', 'AdminStepResource', 'AdminFieldResource', 'AdminFieldTemplateResource', 'AdminUserResource', 'AdminReceiverResource', 'AdminNodeResource', 'AdminNotificationResource', 'AdminShorturlResource', 'FieldAttrs',
    function(GLResource, $q, AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminReceiverResource, AdminNodeResource, AdminNotificationResource, AdminShorturlResource, FieldAttrs) {
  return function(fn) {
      var self = this;

      self.node = AdminNodeResource.get();
      self.contexts = AdminContextResource.query();
      self.questionnaires = AdminQuestionnaireResource.query();
      self.fieldtemplates = AdminFieldTemplateResource.query();
      self.users = AdminUserResource.query();
      self.receivers = AdminReceiverResource.query();
      self.notification = AdminNotificationResource.get();
      self.shorturls = AdminShorturlResource.query();

      self.field_attrs = FieldAttrs.get().$promise.then(function(field_attrs) {
        self.field_attrs = field_attrs;
        self.get_field_attrs = function(type) {
          if (type in self.field_attrs) {
            return self.field_attrs[type];
          } else {
            return {};
          }
        };
      });

      $q.all([self.node.$promise,
              self.contexts.$promise,
              self.field_attrs.$promise,
              self.questionnaires.$promise,
              self.fieldtemplates.$promise,
              self.receivers.$promise,
              self.notification.$promise,
              self.shorturls.$promise]).then(function() {
        fn(this);
      });
    };
}]).
  factory('UserPreferences', ['GLResource', function(GLResource) {
    return new GLResource('preferences', {}, {'update': {method: 'PUT'}});
}]).
  factory('TipOverview', ['GLResource', function(GLResource) {
    return new GLResource('admin/overview/tips');
}]).
  factory('FileOverview', ['GLResource', function(GLResource) {
    return new GLResource('admin/overview/files');
}]).
  factory('StatsCollection', ['GLResource', function(GLResource) {
    return new GLResource('admin/stats/:week_delta', {week_delta: '@week_delta'}, {});
}]).
  factory('AnomaliesCollection', ['GLResource', function(GLResource) {
    return new GLResource('admin/anomalies');
}]).
  factory('ActivitiesCollection', ['GLResource', function(GLResource) {
    return new GLResource('admin/activities/details');
}]).
  factory('StaticFiles', ['GLResource', function(GLResource) {
    return new GLResource('admin/staticfiles');
}]).
  factory('DefaultL10NResource', ['GLResource', function(GLResource) {
    return new GLResource('l10n/:lang.json', {lang: '@lang'});
}]).
  factory('Utils', ['$rootScope', '$location', '$filter', '$sce', '$uibModal', 'Authentication',
  function($rootScope, $location, $filter, $sce, $uibModal, Authentication) {
    return {
      getXOrderProperty: function() {
        return 'x';
      },

      getYOrderProperty: function(elem) {
        var key = 'presentation_order';
        if (elem[key] === undefined) {
          key = 'y';
        }
        return key;
      },

      dumb_function: function() {
        return true;
      },

      iframeCheck: function() {
        try {
          return window.self !== window.top;
        } catch (e) {
          return true;
        }
      },

      base64ToTrustedScriptUrl: function(base64_data) {
        return $sce.trustAsResourceUrl('data:application/javascript;base64,' + base64_data);
      },

      update: function (model, cb, errcb) {
        var success = {};
        model.$update(function() {
          $rootScope.successes.push(success);
        }).then(
          function() { if (cb !== undefined){ cb(); } },
          function() { if (errcb !== undefined){ errcb(); } }
        );
      },

      go: function (hash) {
        $location.path(hash);
      },

      randomFluff: function () {
        return Math.random() * 1000000 + 1000000;
      },

      imgDataUri: function(data) {
        if (data === '') {
          data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgDTD2qgAAAAASUVORK5CYII=';
        }

        return 'data:image/png;base64,' + data;
      },

      isHomepage: function () {
        return $location.path() === '/';
      },

      isWizardPage: function () {
        return $location.path() === '/wizard';
      },

      isLoginPage: function () {
        var path = $location.path();
        return (path === '/login' ||
                path === '/admin' ||
                path === '/custodian' ||
                path === '/receipt');
      },

      isWhistleblowerPage: function() {
        var path = $location.path();
        return this.isSubmissionPage() || path === '/status';
      },

      isSubmissionPage: function() {
        var path = $location.path();
        return (path === '/' ||
                path === '/start' ||
                path === '/submission' ||
                path === '/receipt');
      },

      classExtension: function() {
        return {
          'ext-public': this.isWhistleblowerPage(),
          'ext-login': this.isLoginPage(),
          'ext-auth': Authentication.hasUserRole(),
          'ext-embedded': $rootScope.embedded,
        };
      },

      showLoginForm: function () {
        return (!this.isHomepage() &&
                !this.isLoginPage() &&
                !this.isSubmissionPage());
      },

      showPrivacyBadge: function() {
        return (!$rootScope.embedded &&
                !$rootScope.node.disable_privacy_badge &&
                this.isWhistleblowerPage());
      },

      showFilePreview: function(content_type) {
        var content_types = [
          'image/gif',
          'image/jpeg',
          'image/png',
          'image/bmp'
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
          elements = $filter('orderBy')(elements, key);
          angular.forEach(elements, function (element) {
            element[key] = i;
            i += 1;
          });
        }
      },

      exportJSON: function(data, filename) {
        var json = angular.toJson(data, 2);
        var blob = new Blob([json], {type: "application/json"});
        filename = filename === undefined ? 'data.json' : filename;
        saveAs(blob, filename);
      },

      uploadedFiles: function(uploads) {
        var sum = 0;

        angular.forEach(uploads, function(flow) {
          if (flow !== undefined) {
            sum += flow.files.length;
          }
        });

        return sum;
      },

      getUploadStatus: function(uploads) {
        var error = false;

        for (var key in uploads) {
          if (uploads.hasOwnProperty(key)) {
            if (uploads[key].files.length > 0 && uploads[key].progress() != 1) {
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
      },

      isUploading: function(uploads) {
        return this.getUploadStatus(uploads) === 'uploading';
      },

      remainingUploadTime: function(uploads) {
        var sum = 0;

        angular.forEach(uploads, function(flow) {
          var x = flow.timeRemaining();
          if (x === 'Infinity') {
            return 'Infinity';
          }
          sum += x;
        });

        return sum;
      },

      uploadProgress: function(uploads) {
        var sum = 0;
        var n = 0;

        angular.forEach(uploads, function(flow) {
          sum += flow.progress();
          n += 1;
        });

        if (n === 0 || sum === 0) {
          return 1;
        }

        return sum / n;
      },

      openConfirmableModalDialog: function(template, arg, scope) {
        scope = scope === undefined ? $rootScope : scope;

        return $uibModal.open({
          templateUrl: template,
          controller: 'ConfirmableDialogCtrl',
          backdrop: 'static',
          keyboard: false,
          scope: scope,
          resolve: {
            arg: function () {
              return arg;
            }
          }
        });
      }
    }
}]).
  factory('fieldUtilities', ['$filter', 'CONSTANTS', function($filter, CONSTANTS) {
      var getValidator = function(field) {
        var validators = {
          'custom': field.attrs.regexp,
          'none': '',
          'email': CONSTANTS.email_regexp,
          'number': CONSTANTS.number_regexp,
          'phonenumber': CONSTANTS.phonenumber_regexp,
        };

        return validators[field.attrs.input_validation.value];
      };

      var minY = function(arr) {
        return $filter('min')($filter('map')(arr, 'y'));
      };

      var splitRows = function(fields) {
        var rows = $filter('groupBy')(fields, 'y');
        rows = $filter('toArray')(rows);
        rows = $filter('orderBy')(rows, minY);
        return rows;
      };

      var prepare_field_answers_structure = function(field) {
        if (field.answers_structure === undefined) {
          field.answer_structure = {};
          if (field.type === 'fieldgroup') {
            angular.forEach(field.children, function(child) {
              field.answer_structure[child.id] = [prepare_field_answers_structure(child)];
            });
          }
        }

        return field.answer_structure;
      };

      var isStepTriggered = function(step, answers, score) {
        if (step.triggered_by_score > score) {
          return false;
        }

        if (step.triggered_by_options.length === 0) {
          return true;
        }

        for (var i=0; i<step.triggered_by_options.length; i++) {
          if (answers[step.triggered_by_options[i].field] === undefined) {
            continue
          }

          if (step.triggered_by_options[i].option === answers[step.triggered_by_options[i].field][0]['value']) {
            return true;
          }
        }

        return false;
      };

      var isFieldTriggered = function(field, answers, score) {
        if (field.triggered_by_score > score) {
          return false;
        }

        if (field.triggered_by_options.length === 0) {
          return true;
        }

        for (var i=0; i<field.triggered_by_options.length; i++) {
          if (answers[field.triggered_by_options[i].field] === undefined) {
            continue;
          }

          if (field.triggered_by_options[i].option === answers[field.triggered_by_options[i].field][0]['value']) {
            return true;
          }
        }

        return false;
      };

      return {
        getValidator: getValidator,
        splitRows: splitRows,
        prepare_field_answers_structure: prepare_field_answers_structure,
        isStepTriggered: isStepTriggered,
        isFieldTriggered: isFieldTriggered
      };
}]).
  constant('CONSTANTS', {
     /* The email regexp restricts email addresses to less than 400 chars. See #1215 */
     "email_regexp": /^(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}[\w]{1,100})$/,
     "number_regexp": /^\d+$/,
     "phonenumber_regexp": /^[\+]?[\ \d]+$/,
     "https_regexp": /^(https:\/\/([a-z0-9-]+)\.(.*)$|^)$/,
     "http_or_https_regexp": /^(http(s?):\/\/([a-z0-9-]+)\.(.*)$|^)$/,
     "tor_regexp": /^http(s?):\/\/[0-9a-z]{16}\.onion$/,
     "shortener_shorturl_regexp": /\/s\/[a-z0-9]{1,30}$/,
     "shortener_longurl_regexp": /\/[a-z0-9#=_&?/-]{1,255}$/
}).
  config(['$httpProvider', function($httpProvider) {
    $httpProvider.interceptors.push('globalInterceptor');
}]).
  factory('GLTranslate', ['$translate', '$location','tmhDynamicLocale',
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
    'zh': ['CN', 'TW'], 
    'pt': ['BR', 'PT'],
    'nb': 'NO',
    'hr': 'HR',
    'hu': 'HU',
  };

  var indirect = {
    appLanguage: null,
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
    if (typeof s !== 'string') {
      return '';
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
        return iso_lang + '_' + t[0];
      }
      return iso_lang + '_' + t;

    } else {
      return iso_lang;
    }
  }

  function validLang(inp) {
    // Check for valid looking ISOish language string.
    if (typeof inp !== 'string' || !/^([a-z]{2})(_[A-Z]{2})?$/.test(inp)) {
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
    var useRightToLeft = ["ar", "he", "ur"].indexOf(lang) !== -1;
    document.getElementsByTagName("html")[0].setAttribute('dir', useRightToLeft ? 'rtl' : 'ltr');

    // Update the $translate module to use the new language.
    $translate.use(lang).then(function() {
      // TODO reload the new translations returned by node.
    });

    // For languages that are of the form 'zh_TW', handle the mapping of 'lang'
    // to angular-i18n locale name as best we can. For example: 'zh_TW' becomes 'zh-tw'
    var t = lang;
    if (lang.length === 5) {
      // Angular-i18n's format is typically 'zh-tw'
      t = lang.replace('_', '-').toLowerCase();
    }

    tmhDynamicLocale.set(t); 
  }


  // setLang either uses the current indirect.appLanguage or the passed value
  // to set the language for the entire application.
  function setLang(choice) {
    if (angular.isUndefined(choice)) {
      choice = indirect.appLanguage;
    }

    if (validLang(choice)) {
      facts.userChoice = choice;
      determineLanguage();
    }
  }

  function checkEnabledLanguages(language) {
    return !angular.isDefined(facts.nodeDefault) || enabledLanguages.indexOf(language) !== -1;
  }

  // bestLanguage returns the best language for the application to use given
  // all of the state the GLTranslate service has collected in facts. It picks
  // the language in the order that the properties of the 'facts' object is
  // defined.
  // { object -> string }
  function bestLanguage(facts) {
    if (angular.isDefined(facts.userChoice) &&
        checkEnabledLanguages(facts.browserSniff)) {
      return facts.userChoice;
    } else if (angular.isDefined(facts.urlParam) &&
               checkEnabledLanguages(facts.browserSniff)) {
      return facts.urlParam;
    } else if (angular.isDefined(facts.userPreference) &&
               checkEnabledLanguages(facts.browserSniff)) {
      return facts.userPreference;
    } else if (angular.isDefined(facts.browserSniff) &&
               checkEnabledLanguages(facts.browserSniff)) {
      return facts.browserSniff;
    } else if (angular.isDefined(facts.nodeDefault)) {
      return facts.nodeDefault;
    } else {
      return null;
    }
  }

  // determineLanguage contains all of the scope creeping ugliness of the 
  // factory. It finds the best language to use, changes the appLanguage 
  // pointer, and notifies the dependent services of the change.
  function determineLanguage() {
    indirect.appLanguage = bestLanguage(facts);
    if (indirect.appLanguage !== null) {
      updateTranslationServices(indirect.appLanguage);
    }
  }

  return {
    // Use indirect object to preserve the reference to appLanguage across scopes.
    indirect: indirect,

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
