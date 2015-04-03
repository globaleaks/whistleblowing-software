"use strict";

angular.module('resourceServices.authentication', [])
  .factory('Authentication', ['$http', '$location', '$routeParams',
                              '$rootScope', '$timeout', 'pkdf',
    function($http, $location, $routeParams, $rootScope, $timeout, pkdf) {
      function Session(){
        var self = this;

        var setCookie = function(name, value) {
          /**
           * We set the cookie to be HTTPS only if we are accessing the
           * globaleaks node over HTTPS.
           * If we are not that means that we are accessing it via it's Tor
           * Hidden Service and we don't need to set the cookie HTTPS only as
           * all requests will always be encrypted end to end.
           * */
          $.cookie(name, value);
          if(window.location.protocol === 'https:') {
            $.cookie(name, value, {secure: true});
          }
        };

        $rootScope.login = function(username, password, role, cb) {

          if (role == 'receiver' && password != 'globaleaks') {
            var pwd = pkdf.gl_password(password);
            var passphrase = pkdf.gl_passphrase(password);
            $rootScope.receiver_key_passphrase = passphrase;
            password = pwd;
          }

          return $http.post('/authentication', {'username': username,
                                                'password': password,
                                                'role': role})
            .success(function(response) {
              self.id = response.session_id;
              self.user_id = response.user_id;
              self.username = username;
              self.role = response.role;
              self.session = response.session;
              self.state = response.state;
              self.password_change_needed = response.password_change_needed;

              self.homepage = '';
              self.auth_landing_page = '';

              if (self.role == 'admin') {
                  self.homepage = '/#/admin/landing';
                  self.auth_landing_page = '/admin/landing';
              }
              if (self.role == 'receiver') {
                self.homepage = '/#/receiver/activities';
                if (self.password_change_needed) {
                    self.auth_landing_page = '/receiver/firstlogin';
                } else {
                    self.auth_landing_page = '/receiver/tips';
                }
              }
              if (self.role == 'wb') {
                self.auth_landing_page = '/status';
              }

              if (cb){
                return cb(response);
              }

              if ($routeParams['src']) {
                $location.path($routeParams['src']);

              } else {
                $location.path(self.auth_landing_page);
              }

              $location.search('');

          });
        };

        self.logout_performed = function () {
          var role = self.role;

          self.id = null;
          self.user_id = null;
          self.username = null;
          self.role = null;
          self.session = null;
          self.homepage = null;
          self.auth_langing_page = null;

          if (role === 'wb') {
            $location.path('/');
          } else if (role === 'admin') {
            $location.path('/admin');
          } else {
            $location.path('/login');
          }
        };

        self.receipt = {};

        $rootScope.logout = function() {
          // we use $http['delete'] in place of $http.delete due to
          // the magical IE7/IE8 that do not allow delete as identifier
          // https://github.com/globaleaks/GlobaLeaks/issues/943
          $http['delete']('/authentication').then(self.logout_performed,
                                                  self.logout_performed);

        };

        self.headers = function() {
          var h = {};

          if (self.id) {
            h['X-Session'] = self.id;
          }

          if ($.cookie('XSRF-TOKEN')) {
            h['X-XSRF-TOKEN'] = $.cookie('XSRF-TOKEN');
          }

          if ($rootScope.language) {
            h['GL-Language'] = $rootScope.language;
          }

          return h;
        };

      };

      return new Session;
}]);

angular.module('resourceServices', ['ngResource', 'resourceServices.authentication', 'ui.bootstrap']).
  factory('globalInterceptor', ['$q', '$injector', '$rootScope', '$location',
  function($q, $injector, $rootScope, $location) {
    var requestTimeout = 30000,
      $http = null, $modal = null;

    $rootScope.showRequestBox = false;
    
    function showModal(error) {
      $modal = $modal || $injector.get('$modal');
      var modalInstance = $modal.open({
        templateUrl: 'views/partials/error_popup.html',
        controller: 'ModalCtrl',
        resolve: {
          error: function() {
            return error;
          }
        }
      })
    };

    /* This interceptor is responsible for keeping track of the HTTP requests
     * that are sent and their result (error or not error) */
    return function(promise) {

      $http = $http || $injector.get('$http');

      $rootScope.pendingRequests = function () {
        return $http.pendingRequests.length;
      };

      $rootScope.showRequestBox = true;

      return promise.then(function(response) {

        if ($http.pendingRequests.length < 1) {
          $rootScope.showRequestBox = false;
        }

        return response;
      }, function(response) {
        /* 
           When the response has failed write the rootScope
           errors array the error message.
        */

        if ($http.pendingRequests.length < 1) {
          $rootScope.showRequestBox = false;
        }

        var error = {};
        var source_path = $location.path();

        error.message = response.data.error_message;
        error.code = response.data.error_code;
        error.url = response.config.url;
        error.arguments = response.data.arguments;
        
        // In here you should place the error codes that should trigger a modal
        // view.
        if ( ['55', '56', '57'].indexOf(error.code) != -1 ) {
          showModal(error); 
        }

        /* 30: Not Authenticated / 24: Wrong Authentication */
        if (error.code == 30 || error.code == 24) {

          if (error.code == 24) {
              $rootScope.logout();
          } else {
            var redirect_path = '/login';

            // If we are wb on the status page, redirect to homepage
            if (source_path === '/status') {
                redirect_path = '/';
            }
            // If we are admin on the /admin(/*) pages, redirect to /admin
            else if (source_path.indexOf('/admin') === 0) {
                redirect_path = '/admin';
            }

            // Only redirect if we are not alread on the login page
            if ($location.path() !== redirect_path) {
              $location.path(redirect_path);
              $location.search('src='+source_path);
            };
          }
        };

        if (!$rootScope.errors) {
          $rootScope.errors = [];
        }

        $rootScope.errors.push(error);

        return $q.reject(response);
      });
    }
}]).
  factory('GLCache',['$cacheFactory', function ($cacheFactory) {
    return $cacheFactory('GLCache');
}]).
  factory('Node', ['$resource', 'GLCache', function($resource, GLCache) {
    return $resource('/node', {}, {
      get: {
        method: 'GET',
        cache: GLCache
      }
    })
}]).
  factory('Contexts', ['$resource', 'GLCache', function($resource, GLCache) {
    return $resource('/contexts', {}, {
      get: {
        method: 'GET',
        cache: GLCache
      }
    })
}]).
  factory('Receivers', ['$resource', 'GLCache', function($resource, GLCache) {
    return $resource('/receivers', {}, {
      get: {
        method: 'GET',
        cache: GLCache
      }
    })
}]).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', ['$resource', '$filter', '$location', 'Authentication', 'Node', 'Contexts', 'Receivers', 'pkdf', 'whistleblower',
  function($resource, $filter, $location, Authentication, Node, Contexts, Receivers, pkdf, whistleblower) {

    var submissionResource = $resource('/submission/:token_id/',
        {token_id: '@token_id'},
        {submit:
          {method: 'PUT'}
    });

    var isReceiverInContext = function(receiver, context) {

      return receiver.contexts.indexOf(context.id);

    };

    return function(fn, context_id, receivers_ids) {
      /**
       * This factory returns a Submission object that will call the fn
       * callback once all the information necessary for creating a submission
       * has been collected.
       *
       * This means getting the node information, the list of receivers and the
       * list of contexts.
       */
      var self = this,
        forEach = angular.forEach;

      self.contexts = [];
      self.receivers = [];
      self.current_context = undefined;
      self.maximum_filesize = null;
      self.allow_unencrypted = null;
      self.current_context_fields = [];
      self.current_context_receivers = [];
      self.current_submission = null; 
      self.receivers_selected = {};
      self.uploading = false;
      self.receivers_selected_keys = [];
      
      self.whistleblower_key = null;
      self.receipt = pkdf.gl_receipt();

      var setCurrentContextReceivers = function() {
        self.receivers_selected = {};
        self.receivers_selected_keys = [];
        self.current_context_receivers = [];

        forEach(self.receivers, function(receiver) {
          // enumerate only the receivers of the current context and with pgp keys
          if (self.current_context.receivers.indexOf(receiver.id) !== -1 && receiver.pgp_e2e_public) {
            self.current_context_receivers.push(receiver);

            if (!self.current_context.show_receivers) {
                self.receivers_selected[receiver.id] = true;
                return;
            }

            if (receivers_ids) {
              if (receivers_ids.indexOf(receiver.id) != -1) {
                self.receivers_selected[receiver.id] = true;
                return;
              }
            }

            if (receiver.configuration == 'default' && self.current_context.select_all_receivers) {
              self.receivers_selected[receiver.id] = true;
            } else if (receiver.configuration == 'forcefully_selected') {
              self.receivers_selected[receiver.id] = true;
            }
          }

        });
      };

      Node.get(function(node) {
        self.maximum_filesize = node.maximum_filesize;
        self.allow_unencrypted = node.allow_unencrypted;

        Contexts.query(function(contexts){
          self.contexts = contexts;
          if (context_id) {
            self.current_context = $filter('filter')(self.contexts, 
                                                     {"id": context_id})[0];
          }
          if (self.current_context === undefined) {
            self.current_context = $filter('orderBy')(self.contexts, 'presentation_order')[0];
          }
          Receivers.query(function(receivers){
            self.receivers = [];
            forEach(receivers, function(receiver){
              if (receiver.pgp_key_status !== 'enabled') {
                receiver.missing_pgp = true;
              }
              self.receivers.push(receiver);
            });
            setCurrentContextReceivers();
            fn(self); // Callback!
          });
        });
      });

      /**
       * @name Submission.create
       * @description
       * Create a new submission based on the currently selected context.
       *
       * */
      self.create = function(cb) {
        //TODO: encrypt wb_steps here also

        self.current_submission = new submissionResource({
          context_id: self.current_context.id,
          wb_steps: _.clone(self.current_context.steps),
          receivers: [],
          human_captcha_answer: 0,
          wb_e2e_public: "",
          /* at the moment is just a fingerprint of the pubkey */
          wb_signature: ""
        });

        setCurrentContextReceivers();

        self.current_submission.$save(function(submissionID){
          _.each(self.current_context.fields, function(field, k) {
            if (field.type === "checkboxes") {
              self.current_context.fields[k].value = {};
            }
          });
          self.current_submission.wb_steps = _.clone(self.current_context.steps);

          if (cb)
            cb();
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
        if (!self.receivers_selected) {
          return;
        }

        if (!self.current_submission) {
          return;
        }

        // Set the currently selected pgp pub keys
        self.receivers_selected_keys = [];
        _.each(self.receivers_selected, function(selected, id){
          if (selected) {
            _.each(self.receivers, function(receiver){
              if (id == receiver.id) {
                self.receivers_selected_keys.push(receiver.pgp_e2e_public);
              }
            });
          }
        });

        // Set the currently selected receivers
        self.receivers = [];
        // remind this clean the collected list of receiver_id
        self.current_submission.receivers = [];
        _.each(self.receivers_selected, function(selected, id){
          if (selected) {
            self.current_submission.receivers.push(id);
          }
        });

        openpgp.config.show_comment = false;
        openpgp.config.show_version = false;
        whistleblower.generate_key_from_receipt(self.receipt.value,
                                                function(wb_key){
            self.receipt.pgp = wb_key;
            self.whistleblower_key = wb_key;
            self.current_submission.finalize = true;
            self.current_submission.wb_e2e_public = wb_key.publicKeyArmored;
            self.current_submission.wb_signature = wb_key.key.primaryKey.fingerprint;
            self.current_submission.is_e2e_encrypted = true;

            //wb_key.privateKeyArmored;

            console.log('receivers_selected_keys ', self.receivers_selected_keys);
            var receivers_and_wb_keys = [];
            _.each(self.receivers_selected_keys, function(key) {
                var r_key_pub = openpgp.key.readArmored(key).keys[0];
                receivers_and_wb_keys.push(r_key_pub);
            });
            var wb_key_pub = openpgp.key.readArmored(wb_key.publicKeyArmored).keys[0];
            receivers_and_wb_keys.push(wb_key_pub);
            console.log('Submission receivers_and_wb_keys ',
                        receivers_and_wb_keys);

            var wb_steps = JSON.stringify(self.current_submission.wb_steps);
            openpgp.encryptMessage(receivers_and_wb_keys, wb_steps).then( function(pgp_wb_steps) {
                var list_wb_steps = [];
                list_wb_steps.push(pgp_wb_steps);
                self.current_submission.wb_steps = list_wb_steps;

                self.current_submission.$submit(function(result) {
                    if (result) {
                        Authentication.receipt = self.receipt;
                        $location.url("/receipt");
                    }
                });

            });

      });

      };

    };

}]).
  factory('Tip', ['$resource', '$rootScope', 'Receivers', 'ReceiverPreferences',
  function($resource, $rootScope, Receivers, ReceiverPreferences) {

    var tipResource = $resource('/rtip/:tip_id', {tip_id: '@id'}, {update: {method: 'PUT'}});
    var receiversResource = $resource('/rtip/:tip_id/receivers', {tip_id: '@tip_id'}, {});
    var commentsResource = $resource('/rtip/:tip_id/comments', {tip_id: '@tip_id'}, {});
    var messageResource = $resource('/rtip/:tip_id/messages', {tip_id: '@tip_id'}, {});

    return function(tipID, fn) {
      var self = this,
        forEach = angular.forEach;
      self.tip = {};
      openpgp.config.show_comment = false;
      openpgp.config.show_version = false;

      ReceiverPreferences.get(function(preferences){
        // decrypt receiver priv key
        self.privateKey = openpgp.key.readArmored(preferences.pgp_e2e_private).keys[0];
        var ret = self.privateKey.decrypt($rootScope.receiver_key_passphrase);
        console.log('decrypted receiver privateKey ', ret);

        tipResource.get(tipID, function(result){
          self.tip = result;
          //var json_wb_steps = JSON.parse(decr_wb_steps);
          //self.tip.wb_steps = json_wb_steps;
          self.tip.comments = [];
          self.tip.messages = [];

          if (typeof(result.wb_steps[0]) == 'string'
              && result.wb_steps[0].indexOf("-----BEGIN PGP MESSAGE-----") == 0) {
						var pgpMessage = openpgp.message.readArmored(result.wb_steps[0]);
						openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_wb_steps) {
            	var json_wb_steps = JSON.parse(decr_wb_steps);
            	self.tip.wb_steps = json_wb_steps;
            });
          } else {
                self.tip.wb_steps = result.wb_steps;
          }

          receiversResource.query(tipID, function(receiversCollection){
	        self.tip.receivers = receiversCollection;
            self.cleartext_message = '';
            self.cleartext_comment = '';

            // build receivers and wb pub keys list
	        self.receivers_and_wb_keys = [];
            _.each(receiversCollection, function(receiver) {
                var r_key_pub = openpgp.key.readArmored(receiver.pgp_e2e_public).keys[0];
                self.receivers_and_wb_keys.push( r_key_pub );
            });
            var wb_key_pub = openpgp.key.readArmored( self.tip.wb_e2e_public ).keys[0];
            self.receivers_and_wb_keys.push( wb_key_pub );

            self.tip.newComment = function(content) {
              openpgp.encryptMessage(self.receivers_and_wb_keys, content).then( function(pgp_content) {
                var c = new commentsResource(tipID);
                c.content = pgp_content;
                self.clearc = content;
                c.$save(function(newComment) {
                  newComment.content = self.clearc;
                  self.tip.comments.unshift(newComment);
                  self.clearc = '';
                });
              });
            };

            self.tip.newMessage = function(content) {
              openpgp.encryptMessage(self.receivers_and_wb_keys, content).then( function(pgp_content) {
                var m = new messageResource(tipID);
                m.content = pgp_content;
                self.clearm = content; 
                m.$save(function(newMessage) {
                  self.tip.messages.unshift(newMessage);
                  self.clearm = '';
                });
              });
            };

            messageResource.query(tipID, function(messageCollection){
              _.each(messageCollection, function(message) {
                if (typeof(message.content) == 'string'
                    && message.content.indexOf("-----BEGIN PGP MESSAGE-----") == 0) {
                  var pgpMessage = openpgp.message.readArmored(message.content);
                  openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_content) {
                    message.content = decr_content;
                  }, function(error) {
                    message.content = 'decryptMessage error: ', error;
                  });
                }
              });
              self.tip.messages = messageCollection;
              fn(self.tip);
            });

            commentsResource.query(tipID, function(commentsCollection){
              _.each(commentsCollection, function(comment) {
                if (typeof(comment.content) == 'string'
                    && comment.content.indexOf("-----BEGIN PGP MESSAGE-----") == 0) {
                  var pgpMessage = openpgp.message.readArmored(comment.content);
                  openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_content) {
                    comment.content = decr_content;
                  }, function(error) {
                    comment.content = 'decryptMessage error: ', error;
                  });
                }
              });
              self.tip.comments = commentsCollection;
              fn(self.tip);
            });

          }); // receiverResource

        }); // tipResource

      }); // ReceiverPreferences

    };

	}]).
  factory('WBTip', ['$resource', 'Receivers', 'Authentication',
          function($resource, Receivers, Authentication) {

    var forEach = angular.forEach;

    var tipResource = $resource('/wbtip', {}, {update: {method: 'PUT'}});
    var receiversResource = $resource('/wbtip/receivers', {}, {});
    var commentsResource = $resource('/wbtip/comments', {}, {});
    var messageResource = $resource('/wbtip/messages/:id', {id: '@id'}, {});

    return function(fn) {
      var self = this;
      self.receipt = Authentication.receipt;
      self.tip = {};
      var keyPair = self.receipt.pgp;

      tipResource.get(function(result) {
        var pgpMessage = openpgp.message.readArmored(result.wb_steps[0]);
        self.privateKey = openpgp.key.readArmored(keyPair.privateKeyArmored).keys[0];

        openpgp.config.show_comment = false;
        openpgp.config.show_version = false;
        openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_wb_steps) {

          receiversResource.query(function(receiversCollection) {

            self.tip = result;
            var json_wb_steps = JSON.parse(decr_wb_steps);
            self.tip.wb_steps = json_wb_steps;

            self.tip.comments = [];
            self.tip.messages = [];
            self.tip.receivers = [];
            self.tip.msg_receivers_selector = [];
            self.tip.msg_receiver_selected = null;
            self.tip.receivers = receiversCollection;
            self.receivers_and_wb_keys = [];

            // build receivers and wb pub keys list
            _.each(receiversCollection, function(receiver) {
                var r_key_pub = openpgp.key.readArmored(receiver.pgp_e2e_public).keys[0];
                self.receivers_and_wb_keys.push( r_key_pub );
            });
            var wb_key_pub = openpgp.key.readArmored( self.tip.wb_e2e_public ).keys[0];
            self.receivers_and_wb_keys.push( wb_key_pub );

            self.tip.newComment = function(content) {
              openpgp.encryptMessage(self.receivers_and_wb_keys, content).then( function(pgp_content) {
                var c = new commentsResource();
                c.content = pgp_content;
                self.clearc = content;
                c.$save(function(newComment) {
                  newComment.content = self.clearc;
                  self.tip.comments.unshift(newComment);
                  self.clearc = '';
                });
              });
            };

            self.tip.newMessage = function(content) {
              openpgp.encryptMessage(self.receivers_and_wb_keys, content).then( function(pgp_content) {
                var m = new messageResource({id: self.tip.msg_receiver_selected});
                m.content = pgp_content;
                self.clearm = content;
                m.$save(function(newMessage) {
                  self.tip.messages.unshift(newMessage);
                  self.clearm = '';
                });
              });
            };

            self.tip.updateMessages = function () {
              if (self.tip.msg_receiver_selected) {
                messageResource.query({id: self.tip.msg_receiver_selected}, function (messageCollection) {
                  _.each(messageCollection, function(message) {
                    if ( message.content.indexOf("-----BEGIN PGP MESSAGE-----") > -1 ) {
                      var pgpMessage = openpgp.message.readArmored(message.content);
                      openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_content) {
                        message.content = decr_content;
                      });
                    }
                  });
                  self.tip.messages = messageCollection;
                });
              };
            };

            commentsResource.query({}, function(commentsCollection){
              _.each(commentsCollection, function(comment) {
                if (typeof(comment.content) == 'string'
                    && comment.content.indexOf("-----BEGIN PGP MESSAGE-----") == 0) {
                  var pgpMessage = openpgp.message.readArmored(comment.content);
                  openpgp.decryptMessage(self.privateKey, pgpMessage).then(function(decr_content) {
                    comment.content = decr_content;
                  }, function(error) {
                    comment.content = 'decryptMessage error: ', error;
                  });
                }
              });
              self.tip.comments = commentsCollection;
              fn(self.tip);
            });

            Receivers.query(function(receivers) {
              forEach(self.tip.receivers, function(r1) {
                forEach(receivers, function(r2) {
                  if (r2.id == r1.id) {
                    self.tip.msg_receivers_selector.push({
                      key: r2.id,
                      value: r2.name
                    });
                  }
                });
              });
            });

            fn(self.tip);
          });

        }); //openpgp decrypt

      });

    };
}]).
  factory('WBReceipt', ['$rootScope', 'Authentication', 'whistleblower',
    function($rootScope, Authentication, whistleblower){
    return function(keycode, fn) {
      function login() {
        console.log(Authentication.receipt);
        var fp = Authentication.receipt.pgp.key.primaryKey.fingerprint;
        $rootScope.login('', fp, 'wb',
                         function() {
          fn();
        });
      }
      var self = this;
      if (Authentication.receipt.pgp) {
        login();
      } else {
        whistleblower.generate_key_from_receipt(keycode,
                                                function(key){
          Authentication.receipt.pgp = key;
          login();
        });
      }
    };
}]).
  factory('ReceiverPreferences', ['$resource', function($resource) {
    return $resource('/receiver/preferences', {}, {'update': {method: 'PUT'}});
}]).
  factory('ReceiverTips', ['$resource', function($resource) {
    return $resource('/receiver/tips', {}, {'update': {method: 'PUT'}});
}]).
  factory('ReceiverNotification', ['$resource', function($resource) {
    return $resource('/receiver/notifications');
}]).
  factory('ReceiverOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/users');
}]).
  factory('Admin', ['$resource', function($resource) {
    var self = this,
      forEach = angular.forEach;

    function Admin() {
      var self = this,
        adminContextsResource = $resource('/admin/contexts'),
        adminContextResource = $resource('/admin/context/:context_id',
          {context_id: '@id'},
          {
            update: {
              method: 'PUT'
            }
          }
        ),
        adminFieldsResource = $resource('/admin/fields'),
        adminFieldResource = $resource('/admin/field/:field_id', 
          {field_id: '@id'},
          {
            update: {
              method: 'PUT' 
            }
          }
        ),
        adminFieldTemplatesResource = $resource('/admin/fieldtemplates'),
        adminFieldTemplateResource = $resource('/admin/fieldtemplate/:template_id',
          {template_id: '@id'},
          {
            update: {
              method: 'PUT' 
            }
          }
        ),
        adminReceiversResource = $resource('/admin/receivers'),
        adminReceiverResource = $resource('/admin/receiver/:receiver_id',
          {receiver_id: '@id'},
          {
            update: {
              method: 'PUT'
            }
          }
        ),
        adminNodeResource = $resource('/admin/node', {}, {update: {method: 'PUT'}}),
        adminNotificationResource = $resource('/admin/notification', {}, {update: {method: 'PUT'}});

      adminNodeResource.prototype.toString = function() { return "Admin Node"; };
      adminContextsResource.prototype.toString = function() { return "Admin Contexts"; };
      adminContextResource.prototype.toString = function() { return "Admin Context"; };
      adminFieldResource.prototype.toString = function() { return "Admin Field"; };
      adminFieldsResource.prototype.toString = function() { return "Admin Fields"; };
      adminFieldTemplateResource.prototype.toString = function() { return "Admin Field Template"; };
      adminFieldTemplatesResource.prototype.toString = function() { return "Admin Field Templates"; };
      adminReceiversResource.prototype.toString = function() { return "Admin Receivers"; };
      adminReceiverResource.prototype.toString = function() { return "Admin Receiver"; };
      adminNotificationResource.prototype.toString = function() { return "Admin Notification"; };

      self.context = adminContextResource;
      self.contexts = adminContextsResource.query();

      self.new_context = function() {
        var context = new adminContextResource;
        context.name = "";
        context.description = "";
        context.steps = [];
        context.receivers = [];
        context.select_all_receivers = false;
        context.tip_timetolive = 15;
        context.receiver_introduction = "";
        context.postpone_superpower = false;
        context.can_delete_submission = false;
        context.maximum_selectable_receivers = 0;
        context.show_small_cards = false;
        context.show_receivers = true;
        context.enable_private_messages = true;
        context.presentation_order = 0;
        return context;
      };

      self.template_fields = {};
      self.field_templates = adminFieldTemplatesResource.query(function(){
        angular.forEach(self.field_templates, function(field){
          self.template_fields[field.id] = field;
        });
      });

      self.fields = adminFieldsResource.query();
      
      self.new_field = function(step_id) {
        var field = new adminFieldResource;
        field.label = '';
        field.type = '';
        field.description = '';
        field.is_template = false;
        field.hint = '';
        field.multi_entry = false;
        field.options = [];
        field.required = false;
        field.preview = false;
        field.stats_enabled = false;
        field.x = 0;
        field.y = 0;
        field.children = [];
        field.fieldgroup_id = '';
        field.step_id = step_id;
        return field;
      };

      self.new_field_from_template = function(template_id, step_id) {
        var field = new adminFieldResource;
        field.step_id = step_id;
        field.template_id = template_id;
        return field.$save();
      };

      self.new_field_template = function () {
        var field = new adminFieldTemplateResource;
        field.label = '';
        field.type = '';
        field.description = '';
        field.is_template = true;
        field.hint = '';
        field.multi_entry = false;
        field.options = [];
        field.required = false;
        field.preview = false;
        field.stats_enabled = false;
        field.x = 0;
        field.y = 0;
        field.children = [];
        field.fieldgroup_id = '';
        field.step_id = '';
        return field;
      };

      self.fill_default_field_options = function(field) {
        if (field.type == 'tos') {
          field.options.push({'attrs':
            {
              'clause': '',
              'agreement_statement': ''
            }
          });
        }
      }

      self.receiver = adminReceiverResource;
      self.receivers = adminReceiversResource.query();

      self.new_receiver = function () {
        var receiver = new adminReceiverResource;
        receiver.password = '';
        receiver.contexts = [];
        receiver.description = '';
        receiver.mail_address = '';
        receiver.ping_mail_address = '';
        receiver.can_delete_submission = false;
        receiver.postpone_superpower = false;
        receiver.tip_notification = true;
        receiver.ping_notification = false;
        receiver.pgp_key_info = '';
        receiver.pgp_key_fingerprint = '';
        receiver.pgp_key_remove = false;
        receiver.pgp_key_public = '';
        receiver.pgp_key_expiration = '';
        receiver.pgp_key_status = 'ignored';
        receiver.pgp_enable_notification = false;
        receiver.pgp_key_public = '';
        receiver.pgp_e2e_public = '';
        receiver.pgp_e2e_private = '';
        receiver.presentation_order = 0;
        receiver.state = 'enable';
        receiver.configuration = 'default';
        receiver.password_change_needed = true;
        receiver.language = 'en';
        receiver.timezone = '0';
        return receiver;
      };

      self.node = adminNodeResource.get(function(){
        self.node.password = '';
        self.node.old_password = '';
      });

      self.fieldtemplate = adminFieldTemplateResource;
      self.field = adminFieldResource;

      self.notification = adminNotificationResource.get();
    }
    return Admin;

}]).
  factory('TipOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/tips');
}]).
  factory('FileOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/files');
}]).
  factory('StatsCollection', ['$resource', function($resource) {
    return $resource('/admin/stats/:week_delta', {week_delta: '@week_delta'}, {});
}]).
  factory('AnomaliesCollection', ['$resource', function($resource) {
    return $resource('/admin/anomalies');
}]).
  factory('AnomaliesHistCollection', ['$resource', function($resource) {
    return $resource('/admin/history');
}]).
  factory('ActivitiesCollection', ['$resource', function($resource) {
    return $resource('/admin/activities/details');
}]).
  factory('StaticFiles', ['$resource', function($resource) {
    return $resource('/admin/staticfiles');
}]).
  factory('DefaultAppdata', ['$resource', function($resource) {
    return $resource('/data/appdata_l10n.json', {});
}]).
  factory('cookiesEnabled', function(){

  return function() {

    var enabled = false;
    document.cookie = 'cookiesenabled=true;';
    if (document.cookie == "") {
      enabled = false;
    } else {
      enabled = true;
      $.removeCookie('cookiesenabled');
    }
    return enabled;
  }
}).
  factory('passwordWatcher', ['$parse', function($parse) {
    return function(scope, password) {
      /** This is used to watch the new password and check that is
       *  effectively the same. Sets a local variable mismatch_password.
       *
       *  @param {obj} scope the scope under which we should register watchers
       *                     and insert the mismatch_password field.
       *  @param {string} old_password the old password model name.
       *  @param {string} password the new password model name.
       *  @param {string} check_password need to be equal to the new password.
       **/
      scope.mismatch_password = false;
      scope.unsafe_password = false;
      scope.pwdValidLength = true;
      scope.pwdHasLetter = true;
      scope.pwdHasNumber = true;

      var validatePasswordChange = function () {
        if (scope.$eval(password) !== undefined && scope.$eval(password) != '') {
          scope.pwdValidLength = ( scope.$eval(password)).length >= 8;
          scope.pwdHasLetter = ( /[A-z]/.test(scope.$eval(password))) ? true : false;
          scope.pwdHasNumber = ( /\d/.test(scope.$eval(password))) ? true : false;
          scope.unsafe_password = !(scope.pwdValidLength && scope.pwdHasLetter && scope.pwdHasNumber);
        } else {
          /*
           * This values permits to not show errors when
           * the user has not yed typed any password.
           */
          scope.unsafe_password = false;
          scope.pwdValidLength = true;
          scope.pwdHasLetter = true;
          scope.pwdHasNumber = true;
        }
      };

      scope.$watch(password, function(){
          validatePasswordChange();
      }, true);

    }
}]).
  factory('changePasswordWatcher', ['$parse', function($parse) {
    return function(scope, old_password, password, check_password) {
      /** This is used to watch the new password and check that is
       *  effectively the same. Sets a local variable mismatch_password.
       *
       *  @param {obj} scope the scope under which we should register watchers
       *                     and insert the mismatch_password field.
       *  @param {string} old_password the old password model name.
       *  @param {string} password the new password model name.
       *  @param {string} check_password need to be equal to the new password.
       **/

      scope.invalid = true;

      scope.mismatch_password = false;
      scope.missing_old_password = false;
      scope.unsafe_password = false;

      scope.pwdValidLength = true;
      scope.pwdHasLetter = true;
      scope.pwdHasNumber = true;

      var validatePasswordChange = function () {

        if (scope.$eval(password) !== undefined && scope.$eval(password) != '') {
          scope.pwdValidLength = ( scope.$eval(password)).length >= 8;
          scope.pwdHasLetter = ( /[A-z]/.test(scope.$eval(password))) ? true : false;
          scope.pwdHasNumber = ( /\d/.test(scope.$eval(password))) ? true : false;
          scope.unsafe_password = !(scope.pwdValidLength && scope.pwdHasLetter && scope.pwdHasNumber);
        } else {
          /*
           * This values permits to not show errors when
           * the user has not yed typed any password.
           */
          scope.unsafe_password = false;
          scope.pwdValidLength = true;
          scope.pwdHasLetter = true;
          scope.pwdHasNumber = true;
        }

        if (scope.$eval(password) === undefined ||
          scope.$eval(password) === '' ||
          scope.$eval(password) === scope.$eval(check_password)) {
          scope.mismatch_password = false;
        } else {
          scope.mismatch_password = true;
        }

        if (scope.$eval(old_password) !== undefined && (scope.$eval(old_password)).length >= 1) {
          scope.missing_old_password = false;
        } else {
          scope.missing_old_password = true;
        }

        scope.invalid = scope.$eval(password) === undefined ||
          scope.$eval(password) === '' ||
          scope.mismatch_password ||
          scope.unsafe_password ||
          scope.missing_old_password;
      };

      scope.$watch(password, function(){
          validatePasswordChange();
      }, true);

      scope.$watch(old_password, function(){
          validatePasswordChange();
      }, true);

      scope.$watch(check_password, function(){
          validatePasswordChange();
      }, true);

    }
}]).
  constant('CONSTANTS', {
     /* email regexp is an edited version of angular.js input.js in order to avoid domains with not tld */ 
     "email_regexp": /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i,
     "https_regexp": /^(https:\/\/([a-z0-9-]+)\.(.*)$|^)$/,
     "http_or_https_regexp": /^(http(s?):\/\/([a-z0-9-]+)\.(.*)$|^)$/,
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
    $httpProvider.responseInterceptors.push('globalInterceptor');
}]);
