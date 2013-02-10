angular.module('resourceServices', ['ngResource']).
  factory('globaleaksInterceptor', ['$q', '$rootScope', function($q, $rootScope) {
    /* This interceptor is responsible for keeping track of the HTTP requests
     * that are sent and their result (error or not error) */
    return function(promise) {
      if (!$rootScope.pendingRequests) {
        $rootScope.pendingRequests = [];
      };

      console.log("Response!!!!!!!!!!!");
      $rootScope.pendingRequests.push(promise);

      return promise.then(function(response) {
        return response;
      }, function(response) {
        /* When the response has failed write the rootScope errors array the
        * error message. */
        var error = {};
        error.message = response.data.error_message;
        error.code = response.data.error_code;
        error.url = response.config.url;

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
      var self = this,
        forEach = angular.forEach;

      self.contexts = [];
      self.receivers = [];
      self.current_context = {};
      self.selected_language = null;
      self.current_context_receivers = [];
      self.receivers_selected = {};

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
            fn(self);
          });
        });
      });

      self.create = function() {
        var new_submission = new submissionResource({
          context_gus: self.current_context.context_gus,
          wb_fields: {}, files: [], finalize: false, receivers: []
        });

        new_submission.$save(function(submissionID){
          // XXX the backend should return this.
          new_submission.wb_fields = {};
          setReceiversForCurrentContext();
        });

      };

      self.submit = function() {
        if (!$scope.reivers_selected) {
          console.log("Error: No receivers selected!");
          return;
        }

        // Set the submission field values
        _.each($scope.submission.current_context.fields, function(field, k) {
          $scope.submission.wb_fields[field.name] = field.value;
        });

        // Set the currently selected receivers
        $scope.submission.receivers = [];
        _.each($scope.receivers_selected, function(selected, receiver_gus){
          if (selected) {
            $scope.submission.receivers.push(receiver_gus);
          }
        });
        $scope.submission.finalize = true;

        $scope.submission.$submit(function(result){
          if (result) {
            $scope.submission_complete = true;
          }

        });

      };

    };

}]).
  factory('Tip', ['$resource', 'localization', 'Receivers',
          function($resource, localization, Receivers) {
    var receiversResource = $resource('/tip/:tip_id/receivers', {tip_id: '@tip_id'}, {}),
      tipResource = $resource('/tip/:tip_id', {tip_id: '@tip_id'}, {}),
      commentsResource = $resource('/tip/:tip_id/comments', {tip_id: '@tip_id'}, {});

    var receiverWithID = function(receiverID, fn) {
      Receivers.query(function(receiversList) {
        receiver = _.filter(receiversList, function(r){
          if (r.receiver_gus === receiverID) return true
          else return false
        });
        fn(receiver[0]);
      });
    };

    return function(tipID, fn) {
      this.receivers = [];
      this.comments = [];
      this.tip = {};
      receiversResource.query(tipID, function(receiversCollection){

        _.each(receiversCollection, function(receiver){
          receiverWithID(receiver.receiver_gus, function(receiver){
            this.receivers.push(receiver);
          });
        });

        tipResource.get(tipID, function(result){
          this.tip = result;
          this.tip.receivers = receivers;

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
  factory('AdminContexts', ['$resource', function($resource) {
    return $resource('/admin/context/:context_id',
      {context_id: '@context_gus'},
      {update:
          {method: 'PUT'}
      });
}]).
  factory('AdminNotification', function($resource) {
    return $resource('/admin/context/:context_id',
      {context_id: '@context_gus'},
      {update:
          {method: 'PUT'}
      });
}).
  factory('AdminDelivery', function($resource) {
    return $resource('/admin/context/:context_id',
      {context_id: '@context_gus'},
      {update:
          {method: 'PUT'}
      });
}).
  factory('AdminReceivers', function($resource) {
    return $resource('/admin/receiver/:receiver_id',
      {receiver_id: '@receiver_gus'},
      {update:
          {method: 'PUT'}
      });
}).
  factory('AdminNotification', function($resource) {
    return $resource('/admin/notification', {});
}).
  config(function($httpProvider) {
    $httpProvider.responseInterceptors.push('globaleaksInterceptor');
});


angular.module('localeServices', ['resourceServices']).
  factory('localization', function(Node, Contexts, Receivers){
    var localization = {};
});

