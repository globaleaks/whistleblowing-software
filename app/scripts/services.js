'use strict';

angular.module('resourceServices.authentication', ['ngCookies'])
  .factory('Authentication', ['$http', '$location', '$routeParams', '$rootScope', '$cookies',
    function($http, $location, $routeParams, $rootScope, $cookies){
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
          $cookies[name] = value;
          if(window.location.protocol === 'https:') {
            $cookies[name] += '; secure;';
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
              setCookie('role', self.role);

              if (role == 'admin') {
                auth_landing_page = "/admin/content";
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
            var role = $cookies['role'];

            return $http.delete('/authentication')
              .success(function(response){
                self.id = null;
                self.username = null;
                self.user_id = null;

                delete $cookies['session_id'];
                delete $cookies['role'];
                delete $cookies['auth_landing_page'];
                delete $cookies['tip_id'];

                if (role === 'wb')
                  $location.path('/');
                else
                  $location.path('/login');
            });
        };
      };
      return new Session;
}]);
angular.module('resourceServices', ['ngResource', 'ngCookies', 'resourceServices.authentication']).
  factory('globaleaksInterceptor', ['$q', '$rootScope', '$location', '$cookies',
  function($q, $rootScope, $location, $cookies) {
    /* This interceptor is responsible for keeping track of the HTTP requests
     * that are sent and their result (error or not error) */
    return function(promise) {
      if (!$rootScope.pendingRequests) {
        $rootScope.pendingRequests = [];
      };

      $rootScope.pendingRequests.push(promise);

      return promise.then(function(response) {
        return response;
      }, function(response) {
        /* When the response has failed write the rootScope errors array the
        * error message. */
        var error = {},
          source_path = $location.path();

        error.message = response.data.error_message;
        error.code = response.data.error_code;
        error.url = response.config.url;

        if (error.code == 30) {
          delete $cookies['session_id'];
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
        return $q.reject(response);
      });
    }
}]).
  factory('Node', ['$resource', function($resource) {
    return $resource('/node');
}]).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', ['$resource', 'Node', 'Contexts', 'Receivers',
          function($resource, Node, Contexts, Receivers) {

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
      self.selected_language = null;
      self.current_context_receivers = [];
      self.receivers_selected = {};
      self.completed = false;
      self.receipt = null;

      var setCurrentContextReceivers = function() {
        self.current_context_receivers = [];
        forEach(self.receivers, function(receiver){
          // enumerate only the receivers of the current context
          if (self.current_context.receivers.indexOf(receiver.receiver_gus) !== -1) {
            self.current_context_receivers.push(receiver);
            self.receivers_selected[receiver.receiver_gus] = true;
          };
        });
      };

      Node.get(function(node_info) {
        self.selected_language = node_info.languages[0].code;

        Contexts.query(function(contexts){
          self.contexts = contexts;
          self.current_context = self.contexts[0];
          Receivers.query(function(receivers){
            self.receivers = receivers;
            setCurrentContextReceivers();
          });
          fn(self);
        });
      });

      /**
       * @name Submission.create
       * @description
       * Create a new submission based on the currently selected context.
       *
       * */
      self.create = function() {
        self.current_submission = new submissionResource({
          context_gus: self.current_context.context_gus,
          wb_fields: {}, files: [], finalize: false, receivers: []
        });

        self.current_submission.$save(function(submissionID){
          // XXX the backend should return this.
          setCurrentContextReceivers();
          self.current_submission.wb_fields = {};
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
          self.current_submission.wb_fields[field.name] = field.value;
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
      tipResource = $resource('/tip/:tip_id', {tip_id: '@tip_id'}, {}),
      commentsResource = $resource('/tip/:tip_id/comments', {tip_id: '@tip_id'}, {});

    return function(tipID, fn) {
      var self = this;
      self.tip = {};
      self.tip.comments = [];
      self.tip.receivers = [];


      tipResource.get(tipID, function(result){

        receiversResource.query(tipID, function(receiversCollection){

          self.tip = result;
          console.log(result);
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
      console.log(tip_id);

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

  var deleteCookie = function(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  }

  return function() {
    var enabled = false;
    document.cookie = 'cookiesenabled=true;';
    if (document.cookie == "") {
      enabled = false;
    } else {
      enabled = true;
      deleteCookie('cookiesenabled');
    }
    return enabled;
  }

}).
  factory('changePasswordWatcher', ['$parse', function($parse) {
    return function(scope, old_password, new_password) {
      /** This is used to watch on the new password and old password models and
       *  set the local scope variable invalid_password if an a new password is
       *  set but no old password is provided.
       *
       *  @param {obj} scope the scope under which we should register watchers
       *                     and insert the invalid_password field.
       *  @param {string} old_password the old password model name.
       *  @param {string} new_password the new password model name.
       **/
      scope.invalid_password = false;

      var validatePasswordChange = function() {
        if (scope.$eval(new_password) !== '' && scope.$eval(old_password) === '') {
          scope.invalid_password = true;
        } else {
          scope.invalid_password = false;
        }
      }

      scope.$watch(new_password, function(){
        validatePasswordChange();
      }, true);

      scope.$watch(old_password, function(){
        validatePasswordChange();
      }, true);
    }
}]).
  factory('Admin', ['$resource', function($resource) {

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
        context.description = '';

        context.fields = [];
        // context.languages = [];
        context.receivers = [];

        context.escalation_threshold = 0;
        context.file_max_download = 42;
        context.tip_max_access = 42;
        context.selectable_receiver = true;
        context.tip_timetolive = (3600 * 24) * 15; 
        context.submission_timetolive = (3600 * 24) * 2;

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
        var $cookies = angular.injector(['ngCookies']).get('$cookies');

        if ($cookies['session_id']) {
          headers = angular.extend(headers(),{'X-Session': $cookies['session_id']});
        };
        return data;
    };
    $httpProvider.responseInterceptors.push('globaleaksInterceptor');
    $httpProvider.defaults.transformRequest.push(globaleaksRequestInterceptor);
}]);
