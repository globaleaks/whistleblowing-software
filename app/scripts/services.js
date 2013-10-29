'use strict';

angular.module('resourceServices.authentication', [])
  .factory('Authentication', ['$http', '$location', '$routeParams',
                              '$rootScope', '$timeout',
    function($http, $location, $routeParams, $rootScope, $timeout){
      function Session(){
        var self = this,
          auth_landing_page;

        var setCookie = function(name, value) {
          /**
           * We set the cookie to be https only if we are accessing the
           * globaleaks node over https.
           * If we are not that means that we are accessing it via it's Tor
           * Hidden Service and we don't need to set the cookie https only as
           * all requests will always be encrypted end to end.
           * */
          $.cookie(name, value);
          if(window.location.protocol === 'https:') {
            $.cookie(name, value, {secure: true});
          }
        },

        setExpiration = function(expirationDate) {
          var current_date = new Date();

          setCookie('session_expiration', expirationDate);
          $rootScope.session_expiration = expirationDate;
          $timeout(checkExpiration, expirationDate - current_date);
        },

        checkExpiration = function() {
          var expiration_date = $.cookie('session_expiration');

          if (expiration_date >= current_date) {
            var error = {
              'message': 'Session expired!',
                 'code': 401,
                  'url': $location.path(),
            };

            $rootScope.errors.push(error);

            $timeout(function() {
              $location.path('/login');
              $location.search('src='+source_path);
            }, 3000);

          } else {
            setExpiration(expiration_date);
          }
        };

        self.login = function(username, password, role) {
          return $http.post('/authentication', {'username': username,
                                                'password': password,
                                                'role': role})
            .success(function(response){
              self.id = response.session_id;
              self.user_id = response.user_id;
              self.username = username;
              self.role = role;

              $rootScope.session_id = self.id;
              $rootScope.auth_role = role;
              
              setCookie('session_id', response.session_id);
              setExpiration(response.session_expiration);
              setCookie('role', self.role);

              if (role == 'admin') {
                  if ( password == 'globaleaks') {
                    auth_landing_page = "/admin/password";
                  } else {
                    auth_landing_page = "/admin/overview/tips";
                  }
              }
              if (role == 'receiver') {
                auth_landing_page = "/receiver/tips";
              }
              if (role == 'wb') {
                auth_landing_page = "/status/" + self.user_id;
                setCookie('tip_id', self.user_id);
              }

              setCookie('auth_landing_page', "/#" + auth_landing_page);

              if ($routeParams['src']) {
                $location.path($routeParams['src']);
              } else {
                $location.path(auth_landing_page);
              }

          });
        };

        self.logout = function() {
            var role = $.cookie('role');

            return $http.delete('/authentication')
              .success(function(response){
                self.id = null;
                self.username = null;
                self.user_id = null;

                $.removeCookie('session_id');
                $.removeCookie('role');
                $.removeCookie('auth_landing_page');
                $.removeCookie('tip_id');

                if (role === 'wb')
                  $location.path('/');
                else
                  $location.path('/login');
            });
        };
      };
      return new Session;
}]);
angular.module('resourceServices', ['ngResource', 'resourceServices.authentication']).
  factory('globaleaksInterceptor', ['$q', '$rootScope', '$location',
  function($q, $rootScope, $location) {
    var requestTimeout = 30000;

    $rootScope.showRequestBox = false;

    /* This interceptor is responsible for keeping track of the HTTP requests
     * that are sent and their result (error or not error) */
    return function(promise) {
      if (!$rootScope.pendingRequests)
        $rootScope.pendingRequests = [];

      var Fairy = function(promise) {
        this.promise = promise;
        this.timeout = function() {
          var error = {},
            source_path = $location.path();

          error.message = "Request timed out";
          error.code = 100;
          error.url = '/';

          if (!$rootScope.errors) {
            $rootScope.errors = [];
          }
          $rootScope.errors.push(error);
          $rootScope.pendingRequests.pop(this);
        }
      },
      fairy = new Fairy(promise);

      function timedOut(fairy) {
        return function() {
          fairy.timeout();
          $rootScope.$digest();
        }
      }
      
      $rootScope.$watch('pendingRequests', function(){
        if ($rootScope.pendingRequests.length === 0) {
          $rootScope.showRequestBox = false;
        } else {
          $rootScope.showRequestBox = true;
        }
      }, true);

      $rootScope.pendingRequests.push(promise);

      window.setTimeout(timedOut(fairy), requestTimeout);

      return promise.then(function(response) {

        fairy.timeout = function() {
          // We override the instance method if the promise actually works.
          return true;
        };

        $rootScope.pendingRequests.pop(promise);
        return response;
      }, function(response) {
        /* When the response has failed write the rootScope errors array the
        * error message. */
        var error = {},
          source_path = $location.path();

        error.message = response.data.error_message;
        error.code = response.data.error_code;
        error.url = response.config.url;
        error.arguments = response.data.arguments;

        if (error.code == 30) {
          $.removeCookie('session_id');
          // Only redirect if we are not on the login page
          if ($location.path().indexOf('/login') === -1) {
            $location.path('/login');
            $location.search('src='+source_path);
          };
        };

        if (!$rootScope.errors) {
          $rootScope.errors = [];
        }
        $rootScope.errors.push(error);

        $rootScope.pendingRequests.pop(promise);
        return $q.reject(response);
      });
    }
}]).
  factory('Node', ['$resource', function($resource) {
    return $resource('/node');
}]).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', ['$rootScope', '$resource', 'Node', 'Contexts', 'Receivers',
          function($rootScope, $resource, Node, Contexts, Receivers) {

    var submissionResource = $resource('/submission/:submission_id/',
        {submission_id: '@submission_gus'},
        {submit:
          {method: 'PUT'}
    });

    var isReceiverInContext = function(receiver, context) {

      if (receiver.contexts.indexOf(context.context_gus)) {
        return true;
      } else {
        return false
      };

    };

    return function(fn) {
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
      self.current_context = {};
      self.maximum_filesize = null;
      self.current_context_receivers = [];
      self.receivers_selected = {};
      self.completed = false;
      self.receipt = null;

      var setCurrentContextReceivers = function() {
        self.receivers_selected = {};
        self.current_context_receivers = [];
        forEach(self.receivers, function(receiver){
          // enumerate only the receivers of the current context
          if (self.current_context.receivers.indexOf(receiver.receiver_gus) !== -1) {
            self.current_context_receivers.push(receiver);
            self.receivers_selected[receiver.receiver_gus] = true;
            if ( self.current_context.select_all_receivers == false ) {
              self.receivers_selected[receiver.receiver_gus] = false;
            }
          };
        });
      };

      Node.get(function(node_info) {
        self.maximum_filesize = node_info.maximum_filesize;

        Contexts.query(function(contexts){
          self.contexts = contexts;
          self.current_context = self.contexts[0];
          Receivers.query(function(receivers){
            self.receivers = receivers;
            setCurrentContextReceivers();
            fn(self);
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
        self.current_submission = new submissionResource({
          context_gus: self.current_context.context_gus,
          wb_fields: {}, files: [], finalize: false, receivers: []
        });

        setCurrentContextReceivers();

        self.current_submission.$save(function(submissionID){
          _.each(self.current_context.fields, function(field, k) {
            if (field.type === "checkboxes") {
              self.current_context.fields[k].value = {};
            }
          });
          self.current_submission.wb_fields = {};
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
          console.log("Error: No receivers selected!");
          return;
        };

        if (!self.current_submission) {
          console.log("Error: No current submission!");
        };

        // Set the submission field values
        _.each(self.current_context.fields, function(field, k) {
          self.current_submission.wb_fields[field.key] = field.value;
        });

        // Set the currently selected receivers
        self.receivers = [];
        _.each(self.receivers_selected, function(selected, receiver_gus){
          if (selected) {
            self.current_submission.receivers.push(receiver_gus);
          }
        });
        self.current_submission.finalize = true;

        self.current_submission.$submit(function(result){
          // The submission has completed
          if (result) {
            self.receipt = self.current_submission.receipt;
            self.completed = true;
          };
        });

      };

    };

}]).
  factory('Tip', ['$resource', 'Receivers',
          function($resource, Receivers) {
    var receiversResource = $resource('/tip/:tip_id/receivers', {tip_id: '@tip_id'}, {}),
      tipResource = $resource('/tip/:tip_id', {tip_id: '@id'}, {update: {method: 'PUT'}}),
      commentsResource = $resource('/tip/:tip_id/comments', {tip_id: '@tip_id'}, {});

    return function(tipID, fn) {
      var self = this;
      self.tip = {};
      self.tip.comments = [];
      self.tip.receivers = [];

      tipResource.get(tipID, function(result){

        receiversResource.query(tipID, function(receiversCollection){

          self.tip = result;
          self.tip.receivers = receiversCollection;

          commentsResource.query(tipID, function(commentsCollection){
            self.tip.comments = commentsCollection;
            self.tip.comments.newComment = function(content) {
              var c = new commentsResource(tipID);
              c.content = content;
              c.$save(function(newComment) {
                self.tip.comments.push(newComment);
              });
            };

            // XXX perhaps make this return a lazyly instanced item.
            // look at $resource code for inspiration.
            fn(self.tip);
          });
        });
      });

    };
}]).
  factory('WhistleblowerTip', ['$resource', 'Tip', 'Authentication', function($resource, Tip, Authentication){
    var randomString = function(chars, length) {
      // Generates a random string. Note: this is not cryptographically secure.
      var ret = '';
      for(var i=0;i<length;i++) {
        ret += chars[Math.floor(Math.random()*chars.length)]
      };
      return ret
    };

    var generateRandomTipID = function() {
      // This will generate a random Tip ID that is a UUID4
      var CHARS = ['a', 'b', 'c', 'd', 'e', 'f', '0', '1', '2', '3', '4', '5',
        '6', '7', '8', '9'],
        tip_id = '';

      tip_id += randomString(CHARS, 8);
      tip_id += '-';
      tip_id += randomString(CHARS, 4);
      tip_id += '-';
      tip_id += randomString(CHARS, 4);
      tip_id += '-';
      tip_id += randomString(CHARS, 4);
      tip_id += '-';
      tip_id += randomString(CHARS, 12);

      return tip_id;
    };

    return function(receipt, fn) {
      var self = this,
        tip_id = generateRandomTipID();
      Authentication.login('', receipt, 'wb')
      .then(function() {
        fn(tip_id);
      });
    };
}]).
  factory('Contexts', ['$resource', function($resource) {
    return $resource('/contexts');
}]).
  factory('Receivers', ['$resource', function($resource) {
    return $resource('/receivers');
}]).
  factory('ReceiverPreferences', ['$resource', function($resource) {
    return $resource('/receiver/preferences', {}, {'update': {method: 'PUT'}});
}]).
  factory('ReceiverTips', ['$resource', function($resource) {
    return $resource('/receiver/tips', {}, {'update': {method: 'PUT'}});
}]).
  factory('AdminNode', ['$resource', function($resource) {
    return $resource('/admin/node', {},
      {update:
          {method: 'PUT'}
      });
}]).
  factory('ReceiverOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/users');
}]).
  factory('TipOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/tips');
}]).
  factory('FileOverview', ['$resource', function($resource) {
    return $resource('/admin/overview/files');
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
  factory('notificationRedirect', function(){

  return function() {

    var notification_redirect = false;
    if (document.location.href.indexOf('src=%2Fstatus%2F') > -1) {
      notification_redirect = true;
    }
    return notification_redirect;
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
      scope.unsafe_password = false;
      scope.pwdValidLength = true;
      scope.pwdHasLetter = true;
      scope.pwdHasNumber = true;

      var validatePasswordChange = function() {
        if (scope.$eval(password) !== undefined && scope.$eval(password) != '') {
            scope.pwdValidLength = ( scope.$eval(password)).length >= 8 ? true : false;
            scope.pwdHasLetter = ( /[A-z]/.test(scope.$eval(password) )) ? true : false;
            scope.pwdHasNumber = ( /\d/.test(scope.$eval(password) )) ? true : false;

            if (scope.pwdValidLength && scope.pwdHasLetter && scope.pwdHasNumber) {
              scope.unsafe_password = false;
            } else {
              scope.unsafe_password = true;
            }
        } else {
            /*
             * This values permits to not show errors when
             * the user has not yed typed any password.
             */
            scope.unsafe_password = false
            scope.pwdValidLength = true;
            scope.pwdHasLetter = true;
            scope.pwdHasNumber = true;
        }
      }

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
      scope.mismatch_password = false;
      scope.missing_old_password = false;
      scope.unsafe_password = false;

      scope.pwdValidLength = true;
      scope.pwdHasLetter = true;
      scope.pwdHasNumber = true;

      var validatePasswordChange = function() {

        if (scope.$eval(password) !== undefined && scope.$eval(password) != '') {

            scope.pwdValidLength = ( scope.$eval(password)).length >= 8 ? true : false;
            scope.pwdHasLetter = ( /[A-z]/.test(scope.$eval(password) )) ? true : false;
            scope.pwdHasNumber = ( /\d/.test(scope.$eval(password) )) ? true : false;

            if (scope.pwdValidLength && scope.pwdHasLetter && scope.pwdHasNumber) {
              scope.unsafe_password = false;
            } else {
              scope.unsafe_password = true;
            }
        } else {
            /*
             * This values permits to not show errors when
             * the user has not yed typed any password.
             */
            scope.unsafe_password = false
            scope.pwdValidLength = true;
            scope.pwdHasLetter = true;
            scope.pwdHasNumber = true;
        }

        if ((scope.$eval(password) === undefined) && (scope.$eval(check_password) === undefined)) {
            scope.mismatch_password = false;
        } else {
            if (scope.$eval(password) == scope.$eval(check_password)) {
                scope.mismatch_password = false;
            } else {
                scope.mismatch_password = true;                
            }
        }

        if (scope.$eval(old_password) !== undefined && (scope.$eval(old_password)).length >= 1 )  {
            scope.missing_old_password = false;
        } else {
            scope.missing_old_password = true;
        }
      }

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
  factory('changeParamsWatcher', ['$parse', function($parse) {
    return function(scope) {
        /* To be implemented */
    }
}]).
  factory('Admin', ['$rootScope','$resource', function($rootScope, $resource) {

    function Admin() {
      var self = this,
        adminContextsResource = $resource('/admin/context/:context_id',
          {context_id: '@context_gus'},
          {update:
          {method: 'PUT'}
          }),
        adminReceiversResource = $resource('/admin/receiver/:receiver_id',
          {receiver_id: '@receiver_gus'},
          {update:
          {method: 'PUT'}
          }),
        adminNodeResource = $resource('/admin/node', {}, {update: {method: 'PUT'}}),
        adminNotificationResource = $resource('/admin/notification', {}, {update: {method: 'PUT'}});

      adminContextsResource.prototype.toString = function() { return "Admin Context"; };
      adminReceiversResource.prototype.toString = function() { return "Admin Receiver"; };
      adminNodeResource.prototype.toString = function() { return "Admin Node"; };
      adminNotificationResource.prototype.toString = function() { return "Admin Notification"; };

      self.context = adminContextsResource;
      self.contexts = adminContextsResource.query();

      self.create_context = function(context_name) {
        var context = new adminContextsResource;

        context.name = context_name;
        context.description = "";

        context.fields = [];
        context.receivers = [];

        context.escalation_threshold = 0;
        context.file_max_download = 3;
        context.tip_max_access = 500;
        context.selectable_receiver = true;
        context.select_all_receivers = true;
        context.file_required = false;
        context.tip_timetolive = 15;
        context.submission_timetolive = 48;
        context.receipt_regexp = "[0-9]{10}";
        context.receipt_description = "";
        context.submission_introduction = "";
        context.submission_disclaimer = "";
        context.tags = [];

        context.$save(function(new_context){
          self.contexts.push(new_context);
        });

      };

      self.receiver = adminReceiversResource;
      self.receivers = adminReceiversResource.query();

      self.node = adminNodeResource.get(function(){
        self.node.password = '';
        self.node.old_password = '';
      });

      self.notification = adminNotificationResource.get();
    }
    return Admin;

}]).
  config(['$httpProvider', function($httpProvider) {
    var $rootScope = angular.injector(['ng']).get('$rootScope'),
      globaleaksRequestInterceptor = function(data, headers) {

        var extra_headers = {};

        if ($.cookie('session_id')) {
          extra_headers['X-Session'] = $.cookie('session_id');
        };

        if ($.cookie('XSRF-TOKEN')) {
          extra_headers['X-XSRF-TOKEN'] = $.cookie('XSRF-TOKEN');
        }

        if ($.cookie('language')) {
          extra_headers['GL-Language'] = $.cookie('language');
        };

        headers = angular.extend(headers(), extra_headers);
        return data;
    };
    $httpProvider.responseInterceptors.push('globaleaksInterceptor');
    $httpProvider.defaults.transformRequest.push(globaleaksRequestInterceptor);
}]);
