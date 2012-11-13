// XXX refactor all of this code using
// http://docs.angularjs.org/api/ngResource.$resource

angular.module('nodeRequests', []).
  factory('Node', ['$window', '$http', function($window, $http) {
    return {
      info_node: function() {
        return $http({method: 'GET', url: '/node'})
      }
    }
}]);

angular.module('submissionRequests', []).
  // In here we have all the functions that have to do with performing
  // submission requests to the backend
  factory('Submission', function($window, $http) {
    // This is a factory function responsible for creating functions related
    // to the creation of submissions
    return {
      new_submission: function(context_gus) {
        // This creates a new submission returning the submission ID.
        return $http({method: 'GET', 
          url: '/submission/' + context_gus + '/new'})
      },
      // XXX in
      // https://github.com/globaleaks/GlobaLeaks/wiki/API-Specification it
      // takes receiver_selected in post while it returns receivers_selected
      // in the GET. This should be made uniform.
      update_submission: function(submission_id, 
                           fields, receivers_selected) {
        var request = {};
        if ( typeof(fields) != "undefined" ) {
          request.fields = fields;
        }
        if ( typeof(receivers_selected) != "undefined" ) {
          // XXX should this be receivers_selected or receiver_selected?
          request.receivers_selected = receivers_selected;
        }
        return $http({method: 'POST', 
            url: '/submission/' + submission_id + '/status',
            data: request
        })
      },
      status_submission: function(submission_id) {
         return $http({method: 'GET',
            url: '/submission/' + submission_id + '/status'
        })
      },
      // XXX file is not included here because that is a task for the fileuploader plugin
      finalize_submission: function(submission_id,
            proposed_receipt, folder_name, folder_description) {
        var request = {};
        request.proposed_receipt = proposed_receipt;
        request.folder_name = folder_name;
        request.folder_description = folder_description;

        return $http({method: 'POST',
            url: '/submission/' + submission_id + '/finalize',
            data: request
        })
      }
    }
});

angular.module('tipRequests', []).
  factory('Tip', function($window, $http) {
    return {
      get_tip: function(tip_id) {
        return $http({method: 'GET', url: '/tip/' + tip_id})
      },
      delete_personal_tip: function(tip_id) {
        var request = {};
        request['personal-delete'] = true;
        return $http({method: 'POST', 
            url: '/tip/' + tip_id,
            data: request
        })
      },
      delete_submission_tip: function(tip_id) {
        var request = {};
        request['submission-delete'] = true;
        return $http({method: 'POST', 
            url: '/tip/' + tip_id,
            data: request
        })
      },
      comment_tip: function(tip_id, comment) {
        var request = {};
        request['comment'] = comment;
        return $http({method: 'POST',
            url: '/tip/' + tip_id + '/comment',
            data: request
        })
      },
      // XXX file is not included here because that is a task for the fileuploader plugin
      finalize_tip: function(tip_id, folder_name, 
                        folder_description) {
        var request = {};
        request['folder_name'] = folder_name;
        request['folder_description'] = folder_description;

        return $http({method: 'POST',
            url: '/tip/' + tip_id + '/comment',
            data: request
        })
      }
    }
});

angular.module('receiverRequests', []).
  factory('Receiver', function($window, $http) {
    return {
      info_receiver: function(tip_id) {
        return $http({method: 'GET',
          url: '/receiver/' + tip_id
        })
      },

      get_notification_modules: function(tip_id) {
        return $http({method: 'GET',
          url: '/receiver/' + tip_id + '/notification'
        })
      },
      get_delivery_modules: function(tip_id) {
        return $http({method: 'GET',
          url: '/receiver/' + tip_id + '/delivery'
        })
      },

      update_notification_module: function(tip_id, module_data_dict) {
        return $http({method: 'PUT',
          url: '/receiver/' + tip_id + '/notification'
        })
      },
      update_delivery_module: function(tip_id, module_data_dict) {
        return $http({method: 'PUT',
          url: '/receiver/' + tip_id + '/delivery'
        })
      },

      // XXX do I actually need to pass all the module_data_dict here? Not just
      // a key?
      delete_notification_module: function(tip_id, module_data_dict) {
        return $http({method: 'DELETE',
          url: '/receiver/' + tip_id + '/notification'
        })
      },
      delete_delivery_module: function(tip_id, module_data_dict) {
        return $http({method: 'DELETE',
          url: '/receiver/' + tip_id + '/delivery',
          data: module_data_dict
        })
      },

      create_notification_module: function(tip_id, module_data_dict) {
        return $http({method: 'POST',
          url: '/receiver/' + tip_id + '/notification',
          data: module_data_dict
        })
      },
      create_delivery_module: function(tip_id, module_data_dict) {
        return $http({method: 'POST',
          url: '/receiver/' + tip_id + '/delivery',
          data: module_data_dict
        })
      },
    }
});

angular.module('adminRequests', []).
  factory('Admin', function($window, $http) {
    return {
      get_node_info: function() {
        return $http({method: 'GET', url: '/admin/node'})
      },
      update_node_info: function(node_info) {
        return $http({method: 'POST', 
          url: '/admin/node',
          data: node_info
        })
      },

      get_contexts: function() {
        return $http({method: 'GET',
          url: '/admin/contexts'})
      },
      create_context: function(context_description_dict) {
         return $http({method: 'POST',
          url: '/admin/contexts',
          data: context_description_dict
         })
      },
      // XXX no key to reference what context we are updating?
      // Should the whole list of contexts be sent back to the backend?
      update_context: function(context_description_dict) {
         return $http({method: 'PUT',
          url: '/admin/contexts',
          data: context_description_dict
         })
      },
      delete_context: function(context_description_dict) {
         return $http({method: 'DELETE',
          url: '/admin/contexts',
          data: context_description_dict
         })
      },

      get_receivers: function() {
        return $http({method: 'GET',
          url: '/admin/receivers'})
      },
      create_receiver: function(receiver_description_dict) {
         return $http({method: 'POST',
          url: '/admin/receivers',
          data: receiver_description_dict
         })
      },
      // XXX no key to reference what context we are updating?
      // Should the whole list of receivers be sent back to the backend?
      update_receiver: function(receiver_description_dict) {
         return $http({method: 'PUT',
          url: '/admin/receivers',
          data: receiver_description_dict
         })
      },
      delete_receiver: function(receiver_description_dict) {
         return $http({method: 'DELETE',
          url: '/admin/receivers',
          data: receiver_description_dict
         })
      },

      get_modules: function() {
        return $http({method: 'GET',
          url: '/admin/modules'})
      },
      create_module: function(module_type, module_description_dict) {
         return $http({method: 'POST',
          url: '/admin/modules/' + module_type,
          data: module_description_dict
         })
      },
      // XXX no key to reference what context we are updating?
      // Should the whole list of receivers be sent back to the backend?
      update_module: function(module_type, module_description_dict) {
         return $http({method: 'PUT',
          url: '/admin/modules/' + module_type,
          data: module_description_dict
         })
      },
      delete_module: function(module_type, module_description_dict) {
         return $http({method: 'DELETE',
          url: '/admin/modules/' + module_type,
          data: module_description_dict
         })
      },

    }
});

