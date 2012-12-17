var baseUrl = 'http://127.0.0.1:8082';

angular.module('resourceServices', ['ngResource']).
  factory('Node', function($resource) {
    // XXX this is a quite dirty
    // we probably want to subclass $resource
    var url = '/node';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url, {}, {
      info: {method: 'GET', url: '/node'}
    });
}).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', function($resource) {
    // This is a factory function responsible for creating functions related
    // to the creation of submissions

    var url = '/submission';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url);
}).
  factory('Tip', function($resource) {
    var url = '/tip';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url + '/:tip_id/',
        {tip_id: '@tip_id'}, {
    });
}).
  factory('AdminNode', function($resource) {
    var url = '/admin/node';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url);
}).
  factory('AdminContexts', function($resource) {
    var url = '/admin/contexts';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url);
}).
  factory('AdminReceivers', function($resource) {
    var url = '/admin/receivers';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url);
}).
  factory('AdminModules', function($resource) {
    var url = '/admin/modules';
    if (baseUrl) {
      url = baseUrl + url;
    }

    return $resource(url + '/:module_type',
      {module_type: '@module_type'});
});

angular.module('localeServices', ['resourceServices']).
  factory('localization', function(Node){
    var localization = {};

    if (!localization.node_info) {
      // We set this to the parent scope that that we don't have to make this
      // request again later.
      var node_info = Node.info(function() {
        // Here are functions that are specific to language localization. They
        // are somwhat hackish and I am sure there is a javascript ninja way of
        // doing them.
        // XXX refactor these into something more 1337

        localization.node_info = node_info;
        localization.selected_language =
          localization.node_info.available_languages[0].code;
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

