angular.module('resourceServices', ['ngResource']).
  factory('Node', function($http, $resource) {
    return $resource('/node');
}).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', function($resource) {
    // This is a factory function responsible for creating functions related
    // to the creation of submissions

    return $resource('/submission');
}).
  factory('Tip', function($resource) {
    return $resource('/tip/:tip_id/',
        {tip_id: '@tip_id'}, {
    });
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
  factory('localization', function(Node){
    var localization = {};
    localization.languages = {'en': "English", 'it': "Italiano"};

    if (!localization.node_info) {
      // We set this to the parent scope that that we don't have to make this
      // request again later.
      var node_info = Node.get(function() {
        // Here are functions that are specific to language localization. They
        // are somwhat hackish and I am sure there is a javascript ninja way of
        // doing them.
        // XXX refactor these into something more 1337

        localization.node_info = node_info;
        localization.selected_language =
          localization.node_info.languages[0].code;

        localization.get_node_name = function() {
          return localization.node_info.name[localization.selected_language];
        }

        // Here we add to every context a special function that allows us to
        // retrieve the value of the name and description of the context
        // geolocalized.
        for (var i in localization.node_info.contexts) {
          localization.node_info.contexts[i].get_context_name = function() {
            return this.name[localization.selected_language];
          }
          localization.node_info.contexts[i].get_context_description = function() {
            return this.description[localization.selected_language];
          }
        }

        localization.current_context = localization.node_info.contexts[0];
        // XXX this is somewhat hackish
        localization.current_context_gus = localization.current_context.gus;
      });
    }
    return localization;
});

