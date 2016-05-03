angular.module('GLServices', ['ngResource']).
  factory('GLCache', ['$cacheFactory', function ($cacheFactory) {
    return $cacheFactory('GLCache');
  }]).
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
    ['$http', '$location', '$routeParams', '$rootScope', '$timeout', 'GLTranslate', 'UserPreferences', 'ReceiverPreferences',
    function($http, $location, $routeParams, $rootScope, $timeout, GLTranslate, UserPreferences, ReceiverPreferences) {
      function Session(){
        var self = this;

        $rootScope.login = function(username, password, cb) {
          $rootScope.loginInProgress = true;

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
              GLTranslate.AddUserPreference(prefs.language);
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
            $rootScope.loginInProgress = false;

            if (cb){
              return cb(response);
            }

            if ($routeParams.src) {
              $location.path($routeParams.src);
            } else {
              // Override the auth_landing_page if a password change is needed
              if (self.session.password_change_needed) {
                $location.path('/forcedpasswordchange');
              } else {
                $location.path(self.session.auth_landing_page);
              }
            }

            $location.search('');
          };

          if (username === 'whistleblower') {
            return $http.post('receiptauth', {'receipt': password}).
            success(success_fn).
            error(function() {
              $rootScope.loginInProgress = false;
            });
          } else {
            return $http.post('authentication', {'username': username, 'password': password}).
            success(success_fn).
            error(function() {
              $rootScope.loginInProgress = false;
            });
          }
        };

        self.getLoginUri = function (role, path) {
          var loginUri = "/login";
          if (role === undefined ) {
            if (path === '/status') {
              // If we are whistleblowers on the status page, redirect to homepage
              loginUri = '/';
            } else if (path.indexOf('/admin') === 0) {
              // If we are admins on the /admin(/*) pages, redirect to /admin
              loginUri = '/admin';
            } else if (path.indexOf('/custodian') === 0) {
              // If we are custodians on the /custodian(/*) pages, redirect to /custodian
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

        $rootScope.logout = function() {
          // we use $http['delete'] in place of $http.delete due to
          // the magical IE7/IE8 that do not allow delete as identifier
          // https://github.com/globaleaks/GlobaLeaks/issues/943
          if (self.session.role === 'whistleblower') {
            $http['delete']('receiptauth').then($rootScope.logoutPerformed,
                                                $rootScope.logoutPerformed);
          } else {
            $http['delete']('authentication').then($rootScope.logoutPerformed,
                                                   $rootScope.logoutPerformed);
          }
        };

        $rootScope.loginRedirect = function(sessionExpired) {
          var role = self.session === undefined ? undefined : self.session.role;

          self.session = undefined;

          var source_path = $location.path();

          var redirect_path = self.getLoginUri(role, source_path);

          // Only redirect if we are not already on the login page
          if (source_path !== redirect_path) {
            $location.path(redirect_path);
            if (sessionExpired) {
              $location.search('src=' + source_path);
            }
          }
        };

        $rootScope.logoutPerformed = function() {
          $rootScope.loginRedirect(false);
        };

        self.get_auth_headers = function() {
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
  factory('globalInterceptor', ['$q', '$injector', '$rootScope',
  function($q, $injector, $rootScope) {
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

        try {
          if (response.data !== null) {
            var error = {
              'message': response.data.error_message,
              'code': response.data.error_code,
              'arguments': response.data.arguments
            };

            /* 30: Not Authenticated */
            if (error.code === 30) {
              $rootScope.loginRedirect(true);
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
  factory('Node', ['GLResource', function(GLResource) {
    return new GLResource('node');
}]).
  factory('Contexts', ['GLResource', function(GLResource) {
    return new GLResource('contexts');
}]).
  factory('Receivers', ['GLResource', function(GLResource) {
    return new GLResource('receivers');
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
  factory('Submission', ['$q', 'GLResource', '$filter', '$location', '$rootScope', 'Authentication', 'TokenResource', 'SubmissionResource', 'glbcCipherLib',
      function($q, GLResource, $filter, $location, $rootScope, Authentication, TokenResource, SubmissionResource, glbcCipherLib) {

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
                if ((receiver.pgp_key_fingerprint !== '' || $rootScope.node.allow_unencrypted) ||
                    receiver.configuration !== 'unselectable') {
                  self.receivers_selected[receiver.id] = true;
                }
              }
            } else {
              if (receiver.pgp_key_fingerprint !== '' || $rootScope.node.allow_unencrypted) {
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
                if (receiver.pgp_key_fingerprint !== '' || $rootScope.node.allow_unencrypted) {
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
          encrypted_answers: "",
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
      self.submit = function(answers) {
        if (!self._submission || !self.receivers_selected) {
          return;
        }

        self.done = true;

        self._submission.receivers = [];
        angular.forEach(self.receivers_selected, function(selected, id) {
          if (selected) {
            self._submission.receivers.push(id);
          }
        });

        // TODO redact information from answers before submission
        self._submission.answers = answers;
        
        // Convert _submission.answers to a binary array in a reasonable way.
        var jsonAnswers = JSON.stringify(answers);

        // Attach receiver public keys along with WB public key
        var pubKeys = glbcCipherLib.loadPublicKeys(self.receivers.filter(function (rec) {
          return self._submission.receivers.indexOf(rec.id) > -1;
        }).map(function (rec) {
          return rec.ccrypto_key_public;
        }));

        // Encrypt the payload then Call submission update.
        glbcCipherLib.encryptMsg(jsonAnswers, pubKeys)
        .then(function(ciphertext) {
          self._submission.encrypted_answers = ciphertext.armor();
          // TODO delete answers.
          self._submission.$update(function(result) {
            if (result) {
              Authentication.keycode = self._submission.receipt;
              $location.url("/receipt");
            }
          });
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
// RTipDownloadFile first makes an authenticated get request for the encrypted
// file data. Then it takes that data converts it into an Uint8array, unlocks
// the recipeint's privateKey, decrypts the file and saves it to disk.
 factory('RTipDownloadFile', ['$http', '$filter', 'FileSaver', 'glbcCipherLib', 'glbcKeyRing', function($http, $filter, FileSaver, glbcCipherLib, glbcKeyRing) {
  return function(tip, file) {
    $http({
      method: 'GET',
      url: '/rtip/' + tip.id + '/download/' + file.id,
      responseType: 'blob',
    }).then(function (response) {
      var inputBlob = response.data;
      glbcCipherLib.createArrayFromBlob(inputBlob).then(function(ciphertext) {

        // TODO DELETE ME
        glbcKeyRing.lockKeyRing("fakepassphrase");
        // TODO TODO TODO

        // TODO Get the passphrase from the user or the rootScope!
        glbcKeyRing.unlockKeyRing("fakepassphrase");

        // Decrypt the file
        glbcKeyRing.performDecrypt(ciphertext, 'binary').then(function(plaintext) {

          glbcKeyRing.lockKeyRing("fakepassphrase");

          var outBlob = new Blob([plaintext.data], {type: 'application/octet-stream'});

          // Before saving clean up the filename
          var filename = file.name.slice(0, file.name.length - 4);

          // Save the decrypted file.
          FileSaver.saveAs(outBlob, filename);
        }, function() {
          // Decryption failed. Lock the keyRing.
          glbcKeyRing.lockKeyRing("fakepassphrase");
        });


      });
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
  factory('WhistleblowerTip', ['$rootScope', function($rootScope){
    return function(keycode, fn) {
      $rootScope.login('whistleblower', keycode).then(function() {
        fn();
      });
    };
}]).
  factory('ReceiverPreferences', ['$q', 'GLResource', 'glbcKeyRing', function($q, GLResource, glbcKeyRing) {

    // Extend the default get request to include initialization of the receiver's
    // private key.
    var extendedGet = {
      method: "GET",
      transformResponse: function(data) {
        var prefs = angular.fromJson(data);
        // TODO Temp private key TODO
        var fakefp = "ecaf2235e78e71cd95365843c7b190543caa7585";
        var initRes = glbcKeyRing.initialize(prefs.ccrypto_key_private, fakefp);
        delete prefs.cc_private_key;
        // TODO TODO TODO
        if (initRes) {
          return prefs;
        } else {
          // Throws an error into the globalInterceptor in the format it expects
          var m = "Error initializing recipient's private key";
          var err = new Error(m);
          err.data = {
            'error_message': m,
            'error_code' : 424, // HTTP 424: Failed dependency
            'arguments': [],
          };
          throw err;
        }
      },
    };

    // Create a GlResource with empty params and an extended get action
    return new GLResource('receiver/preferences', {}, {get: extendedGet});
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
  factory('Admin', ['GLResource', '$q', 'AdminContextResource', 'AdminQuestionnaireResource', 'AdminStepResource', 'AdminFieldResource', 'AdminFieldTemplateResource', 'AdminUserResource', 'AdminReceiverResource', 'AdminNodeResource', 'AdminNotificationResource', 'AdminShorturlResource', 'FieldAttrs',
    function(GLResource, $q, AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminReceiverResource, AdminNodeResource, AdminNotificationResource, AdminShorturlResource, FieldAttrs) {
  return function(fn) {
      var self = this;

      self.node = AdminNodeResource.get();
      self.contexts = AdminContextResource.query();
      self.questionnaires = AdminQuestionnaireResource.query();
      self.fieldtemplates = AdminFieldTemplateResource.query();
      self.field_attrs = FieldAttrs.get();
      self.users = AdminUserResource.query();
      self.receivers = AdminReceiverResource.query();
      self.notification = AdminNotificationResource.get();
      self.shorturls = AdminShorturlResource.query();

      $q.all([self.node.$promise,
              self.contexts.$promise,
              self.questionnaires.$promise,
              self.fieldtemplates.$promise,
              self.field_attrs.$promise,
              self.receivers.$promise,
              self.notification.$promise,
              self.shorturls.$promise]).then(function() {

        self.new_context = function() {
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
          context.select_all_receivers = false;
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
          context.receivers = [];
          return context;
        };

        self.new_questionnaire = function() {
          var questionnaire = new AdminQuestionnaireResource();
          questionnaire.id = '';
          questionnaire.key = '';
          questionnaire.name = '';
          questionnaire.show_steps_navigation_bar = true;
          questionnaire.steps_navigation_requires_completion = true;
          questionnaire.steps = [];
          questionnaire.editable = true;
          return questionnaire;
        };

        self.new_step = function(questionnaire_id) {
          var step = new AdminStepResource();
          step.id = '';
          step.label = '';
          step.description = '';
          step.presentation_order = 0;
          step.children = [];
          step.questionnaire_id = questionnaire_id;
          step.triggered_by_score = 0;
          return step;
        };

        self.get_field_attrs = function(type) {
          if (type in self.field_attrs) {
            return self.field_attrs[type];
          } else {
            return {};
          }
        };

        self.new_field = function(step_id, fieldgroup_id) {
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
        };

        self.new_field_from_template = function(template_id, step_id, fieldgroup_id) {
          var field = self.new_field(step_id, fieldgroup_id);
          field.template_id = template_id;
          field.instance = 'reference';
          return field;
        };

        self.new_field_template = function (fieldgroup_id) {
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
        };

        self.new_user = function () {
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
          user.mail_address = '';
          user.pgp_key_fingerprint = '';
          user.pgp_key_remove = false;
          user.pgp_key_public = '';
          user.pgp_key_expiration = '';
          user.language = 'en';
          user.timezone = 0;
          return user;
        };

        self.new_shorturl = function () {
          return new AdminShorturlResource();
        };

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
  factory('DefaultAppdata', ['GLResource', function(GLResource) {
    return new GLResource('data/appdata_l10n.json', {});
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
          if (field.triggered_by_options[i].option === answers[field.triggered_by_options[i].field][0]['value']) {
            return true;
          }
        }
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
     "shortener_longurl_regexp": /\/[a-z0-9#=_&?/-]{1,255}$/,
     "timezones": [
        {"timezone": -12.0, "label": "(GMT -12:00) Eniwetok, Kwajalein"},
        {"timezone": -11.0, "label": "(GMT -11:00) Midway Island, Samoa"},
        {"timezone": -10.0, "label": "(GMT -10:00) Hawaii"},
        {"timezone": -9.0, "label": "(GMT -9:00) Alaska"},
        {"timezone": -8.0, "label": "(GMT -8:00) Pacific Time (US &amp; Canada)"},
        {"timezone": -7.0, "label": "(GMT -7:00) Mountain Time (US &amp; Canada)"},
        {"timezone": -6.0, "label": "(GMT -6:00) Central Time (US &amp; Canada), Mexico City"},
        {"timezone": -5.0, "label": "(GMT -5:00) Eastern Time (US &amp; Canada), Bogota, Lima"},
        {"timezone": -4.0, "label": "(GMT -4:00) Atlantic Time (Canada), Caracas, La Paz"},
        {"timezone": -3.5, "label": "(GMT -3:30) Newfoundland"},
        {"timezone": -3.0, "label": "(GMT -3:00) Brazil, Buenos Aires, Georgetown"},
        {"timezone": -2.0, "label": "(GMT -2:00) Mid-Atlantic"},
        {"timezone": -1.0, "label": "(GMT -1:00 hour) Azores, Cape Verde Islands"},
        {"timezone": 0.0, "label": "(GMT) Western Europe Time, London, Lisbon, Casablanca"},
        {"timezone": 1.0, "label": "(GMT +1:00 hour) Brussels, Copenhagen, Madrid, Paris"},
        {"timezone": 2.0, "label": "(GMT +2:00) Kaliningrad, South Africa"},
        {"timezone": 3.0, "label": "(GMT +3:00) Baghdad, Riyadh, Moscow, St. Petersburg"},
        {"timezone": 3.5, "label": "(GMT +3:30) Tehran"},
        {"timezone": 4.0, "label": "(GMT +4:00) Abu Dhabi, Muscat, Baku, Tbilisi"},
        {"timezone": 4.5, "label": "(GMT +4:30) Kabul"},
        {"timezone": 5.0, "label": "(GMT +5:00) Ekaterinburg, Islamabad, Karachi, Tashkent"},
        {"timezone": 5.5, "label": "(GMT +5:30) Bombay, Calcutta, Madras, New Delhi"},
        {"timezone": 5.75, "label": "(GMT +5:45) Kathmandu"},
        {"timezone": 6.0, "label": "(GMT +6:00) Almaty, Dhaka, Colombo"},
        {"timezone": 7.0, "label": "(GMT +7:00) Bangkok, Hanoi, Jakarta"},
        {"timezone": 8.0, "label": "(GMT +8:00) Beijing, Perth, Singapore, Hong Kong"},
        {"timezone": 9.0, "label": "(GMT +9:00) Tokyo, Seoul, Osaka, Sapporo, Yakutsk"},
        {"timezone": 9.5, "label": "(GMT +9:30) Adelaide, Darwin"},
        {"timezone": 10.0, "label": "(GMT +10:00) Eastern Australia, Guam, Vladivostok"},
        {"timezone": 11.0, "label": "(GMT +11:00) Magadan, Solomon Islands, New Caledonia"},
        {"timezone": 12.0, "label": "(GMT +12:00) Auckland, Wellington, Fiji, Kamchatka"}
     ]
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

  // bestLanguage returns the best language for the application to use given
  // all of the state the GLTranslate service has collected in facts. It picks
  // the language in the order that the properties of the 'facts' object is
  // defined.
  // { object -> string }
  function bestLanguage(facts) {
    if (angular.isDefined(facts.userChoice)) {
      return facts.userChoice;
    } else if (angular.isDefined(facts.urlParam)) {
      return facts.urlParam;
    } else if (angular.isDefined(facts.userPreference)) {
      return facts.userPreference;
    } else if (angular.isDefined(facts.browserSniff) &&
               enabledLanguages.indexOf(facts.browserSniff) !== -1) {
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

    AddNodeFacts: function(defaultLang, languages_enabled) {
      facts.nodeDefault = defaultLang;

      enabledLanguages = languages_enabled;

      determineLanguage();
    },

    AddUserPreference: function(lang) {
      facts.userPreference = lang;
      determineLanguage();
    },

  };
}]);
