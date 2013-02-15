angular.module('resourceServices.authentication', [])
  .factory('Authentication', ['$http', '$location', '$routeParams', '$rootScope',
    function($http, $location, $routeParams, $rootScope){
      function Session(){
        var self = this;

        self.login = function(username, password, role) {
          return $http.post('/login', {'username': username,
                                'password': password,
                                'role': role})
            .success(function(response){
              self.id = response.session_id;
              self.username = username;
              sessionStorage['session_id'] = response.session_id;
              $rootScope.session_id = self.id;
              if (role != 'wb') {
                $location.path($routeParams['src']);
              }
          });
        };

        self.logout = function() {
            sessionStorage.removeItem('session_id');
            return $http.delete('/login')
              .success(function(response){
                self.id = null;
            });
        };
      };
      return new Session;
}]);

angular.module('resourceServices', ['ngResource', 'resourceServices.authentication']).
  factory('globaleaksInterceptor', ['$q', '$rootScope', '$location',
  function($q, $rootScope, $location) {
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
          $location.path('/login');
          $location.search('src='+source_path);
        };

        if (!$rootScope.errors) {
          $rootScope.errors = [];
        }
        $rootScope.errors.push(error);
        return $q.reject(response);
      });
    }
}]).
  factory('Node', function($resource) {
    return $resource('/node');
}).
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

      var setReceiversForCurrentContext = function() {
        // Make sure all the receivers are selected by default
        forEach(self.receivers, function(receiver, idx) {
          // Check if receiver belongs to the currently selected context
          if (isReceiverInContext(receiver, self.current_context)) {
            self.current_context_receivers[idx] = receiver;
            self.receivers_selected[receiver.receiver_gus] = true;
          }
        });
      };

      Node.get(function(node_info) {
        self.selected_language = node_info.languages[0].code;

        Contexts.query(function(contexts){
          self.contexts = contexts;
          Receivers.query(function(receivers){
            self.receivers = receivers;
            setReceiversForCurrentContext();
            self.current_context = self.contexts[0];
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
      self.create = function() {
        self.current_submission = new submissionResource({
          context_gus: self.current_context.context_gus,
          wb_fields: {}, files: [], finalize: false, receivers: []
        });

        self.current_submission.$save(function(submissionID){
          // XXX the backend should return this.
          self.current_submission.wb_fields = {};
          setReceiversForCurrentContext();
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
      this.receivers = [];
      this.comments = [];
      this.tip = {};
      receiversResource.query(tipID, function(receiversCollection){

        tipResource.get(tipID, function(result){
          this.tip = result;
          this.tip.receivers = receiversCollection;

          commentsResource.query(tipID, function(commentsCollection){

            _.each(commentsCollection, function(comment){
              if (comment.author_gus) {
                receiverWithID(comment.author_gus, function(author){
                  comment.author = author;
                });
              }
              this.comments.push(comment);
            });

            this.tip.comments = this.comments;
            this.tip.comments.newComment = function(content) {
              var c = new commentsResource(tipID);
              c.content = content;
              c.$save(function(newComment) {
                if (newComment.author_gus) {
                  receiverWithID(newComment.author_gus, function(author){
                    c.author = author;
                  });
                }
                this.tip.comments.push(newComment);
              });
            };

            // XXX perhaps make this return a lazyly instanced item.
            // look at $resource code for inspiration.
            fn(this.tip);
          });
        });
      });

    };
}]).
  factory('WhistleblowerTip', ['$resource', 'Tip', 'Authentication', function($resource, Tip, Authentication){
    var randomString = function(chars, length) {
      // Generates a random string. Note: this is not cryptographically secure.
      var ret = '';
      for(i=0;i<length;i++) {
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
  factory('Contexts', function($resource) {
    return $resource('/contexts');
}).
  factory('Receivers', function($resource) {
    return $resource('/receivers');
}).
  factory('AdminNode', function($resource) {
    return $resource('/admin/node', {},
      {update:
          {method: 'PUT'}
      });
}).
  factory('Admin', function($resource) {
    function Admin(){
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
        adminNodeResource = $resource('/admin/node', {}, {update: {method: 'PUT'}});

      adminContextsResource.prototype.toString = function() { return "Admin Context"; }
      adminReceiversResource.prototype.toString = function() { return "Admin Receiver"; }
      adminNodeResource.prototype.toString = function() { return "Admin Node"; }

      self.context = adminContextsResource;
      self.contexts = adminContextsResource.query();

      self.create_context = function(context_name) {
        var context = new adminContextsResource;

        context.name = context_name;
        context.description = '';

        context.fields = [];
        context.languages = [];
        context.receivers = [];

        context.escalation_threshold = null;
        context.file_max_download = 42;
        context.tip_max_access = 42;
        context.selectable_receiver = true;
        context.tip_timetolive = 42;

        context.$save(function(new_context){
          self.contexts.push(new_context);
        });

      };

      self.receiver = adminReceiversResource;
      self.receivers = adminReceiversResource.query();

      self.create_receiver = function(receiver_name) {
        var receiver = new adminReceiversResource;

        receiver.name = receiver_name;

        receiver.description = '';
        receiver.password = null;

        receiver.notification_fields = {'mail_address': ''};

        receiver.languages = [];

        // Under here go default settings
        receiver.can_postpone_expiration = true;
        receiver.can_configure_notification = true;
        receiver.can_configure_delivery = true;
        receiver.can_delete_submission = true;

        receiver.receiver_level = 1;

        receiver.tags = [];
        receiver.contexts =  [];

        receiver.$save(function(created_receiver){
          self.receivers.push(created_receiver);
        });
      };

      self.node = adminNodeResource.get(function(){
        self.node.password = '';
        self.node.old_password = '';
      });

    };
    return new Admin;
}).
  config(function($httpProvider) {
    var $rootScope = angular.injector(['ng']).get('$rootScope'),
      globaleaksRequestInterceptor = function(data, headers) {
        if (sessionStorage['session_id']) {
          headers = angular.extend(headers(),{'X-Session': sessionStorage['session_id']});
        };
        return data;
      };
    $httpProvider.responseInterceptors.push('globaleaksInterceptor');
    $httpProvider.defaults.transformRequest.push(globaleaksRequestInterceptor);

});

