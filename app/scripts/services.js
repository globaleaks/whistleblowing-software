angular.module('resourceServices', ['ngResource']).
  factory('Node', function($resource) {
    return $resource('/node');
}).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', function($resource) {
    // This is a factory function responsible for creating functions related
    // to the creation of submissions
    return $resource('/submission/:submission_id/',
        {submission_id: '@submission_gus'},
        {submit:
          {method: 'PUT'}
    });
}).
  factory('Tip', function($resource) {
    return $resource('/tip/:tip_id/',
        {tip_id: '@tip_id'}, {
    });
}).
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
  factory('AdminContexts', function($resource) {
    return $resource('/admin/context/:context_id',
      {context_id: '@context_gus'},
      {update:
          {method: 'PUT'}
      });
}).
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
  factory('AdminModules', function($resource) {
    return $resource('/admin/module/:module_type',
      {module_type: '@module_type'});
});


angular.module('localeServices', ['resourceServices']).
  factory('localization', function(Node, Contexts, Receivers){
    var localization = {};

    if (!localization.node_info) {
      // We set this to the parent scope that that we don't have to make this
      // request again later.
      Node.get(function(node_info) {
        // Here are functions that are specific to language localization. They
        // are somwhat hackish and I am sure there is a javascript ninja way of
        // doing them.
        // XXX refactor these into something more 1337

        localization.node_info = node_info;
        localization.selected_language = localization.node_info.languages[0].code;

        localization.get_node_name = function() {
          //return localization.node_info.name[localization.selected_language];
          return localization.node_info.name;
        }

        // Here we add to every context a special function that allows us to
        // retrieve the value of the name and description of the context
        // geolocalized.
        //
        // for (var i in localization.node_info.contexts) {
        //   localization.node_info.contexts[i].get_context_name = function() {
        //     return this.name[localization.selected_language];
        //   }
        //   localization.node_info.contexts[i].get_context_description = function() {
        //     return this.description[localization.selected_language];
        //   }
        // }

      });
    };

    // XXX refactor using proper caching factory
    if(!localization.current_context) {
      Contexts.query(function(contexts) {
          localization.contexts = contexts;

          Receivers.query(function(receivers) {
            localization.receivers = receivers;
            localization.current_context_receivers = [];
            localization.current_context = localization.contexts[0];
          });
      });
    };
    return localization;
});

