// XXX refactor all of this code using
// http://docs.angularjs.org/api/ngResource.$resource

angular.module('nodeServices', ['ngResource']).
  factory('Node', function($resource) {
    return $resource('/node', {}, {
      info: {method: 'GET', url: '/node'}
    })
});

angular.module('submissionServices', ['ngResource']).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', function($resource) {
    // This is a factory function responsible for creating functions related
    // to the creation of submissions
    return $resource('/submission/:id_or_gus/:action', {action: 'status',
      id_or_gus: '@submission_gus'}, {

      create: {method: 'GET'},
      // XXX in
      // https://github.com/globaleaks/GlobaLeaks/wiki/API-Specification it
      // takes receiver_selected in post while it returns receivers_selected
      // in the GET. This should be made uniform.

      update: {method: 'POST'},
      // XXX file is not included here because that is a task for the fileuploader plugin
      finalize: {method: 'POST'}
    });
});

angular.module('tipServices', ['ngResource']).
  factory('Tip', function($resource) {
    return $resource('/tip/:tip_id/:action',
        {tip_id: '@tip_id'}, {
        // GET and POST of / come for free.
        comment: {method: 'POST',
          params: {action: 'comment'},
        },

        // This takes as the body of the request folder_name,
        finalize: {method: 'POST',
          params: {action: 'finalize'}
        }
    })
      })
});

angular.module('receiverServices', ['ngResource']).
  factory('Receiver', function($resource) {
    return $resource('/receiver/:tip_id',
      {tip_id: '@tip_id'}
    )
}).
  factory('ReceiverNotification', function($resource) {
    // This implements the receiver notification component personalizations
    return $resource('/receiver/:tip_id/notification',
      {tip_id: '@tip_id'}
    )
}).
  factory('ReceiverDelivery', function($resource) {
    // This implements the receiver delivery component personalizations
    return $resource('/receiver/:tip_id/delivery',
      {tip_id: '@tip_id'}
    )
});

angular.module('adminServices', ['ngResource']).
  factory('AdminNode', function($resource) {
    return $resource('/admin/node')
}).
  factory('AdminContexts', function($resource) {
    return $resource('/admin/contexts')
}).
  factory('AdminReceivers', function($resource) {
    return $resource('/admin/receivers')
}).
  factory('AdminModules', function($resource) {
    return $resource('/admin/modules/:module_type',
      {module_type: '@module_type'}
    )
});

angular.module('helpServices', ['ngResource']).
  factory('HelpStrings', function($resource) {
    return $resource('/scripts/help_strings/node_info.json')
});

