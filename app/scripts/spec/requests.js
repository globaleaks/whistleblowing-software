var node = {},
  status = {},
  submission = {};

node.root = function() {
  return {'url': '/node', 'method': 'GET'}
};

status.get = function(receipt) {
  return {'url': '/tip' + receipt,
    'method': 'GET'
  }
};


submission.root = function() {
  return {'url': '/submission',
    'method': 'GET'
  }
};

submission.status_get = function(submission_id) {
  return {'url': '/submission/' + submission_id + '/status',
    'method': 'GET'
  }
};

submission.status_post = function(submission_id, params) {
  return {'url': '/submission/'+ submission_id + '/status',
                'type': 'POST',
                'data': JSON.stringify(params)
  }
};

submission.finalize_post = function(submission_id, proposed_receipt,
                                    folder_name, folder_description) {
  var request = {'proposed_receipt': proposed_receipt,
                 'folder_name': folder_name,
                 'folder_description': folder_description};

  return {'url': '/submission/' + submission_id + '/finalize',
   'type': 'POST',
   'data': JSON.stringify(request)
  }
};

module.exports = node;
module.exports = submission;
module.exports = status;
