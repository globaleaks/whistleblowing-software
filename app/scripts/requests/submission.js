define(['latenza'], function(latenza) {
  return {
    root: function() {
      return latenza.ajax({'url': '/submission',
                'type': 'GET'
      });
    },
    status_get: function(submission_id) {
      return latenza.ajax({'url': '/submission/' + submission_id + '/status',
                'type': 'GET'
      });
    },
    status_post: function(submission_id, params) {
      return latenza.ajax({'url': '/submission/'+ submission_id + '/status',
                'type': 'POST',
                'data': JSON.stringify(params)
      });
    },

    finalize_post: function(submission_id, proposed_receipt, folder_name, folder_description) {
      var request = {'proposed_receipt': proposed_receipt,
                     'folder_name': folder_name,
                     'folder_description': folder_description};

      return latenza.ajax({'url': '/submission/' + submission_id + '/finalize',
                           'type': 'POST',
                           'data': JSON.stringify(request)
      });
    },
  }
});
